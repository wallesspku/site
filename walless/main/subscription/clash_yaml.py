from typing import Dict, Tuple
import time
import copy
from copy import deepcopy
from functools import lru_cache
import shortuuid

import yaml
from walless_utils import data_format, node_pool, cfg

from .rule import Rule
from ..constants import *
from ..models import Push
from ..util import Dumper
from .clash_node import ProxyNode, gen_proxy_nodes, InfoNode, direct_node
from .user_request import UserRequest
from .group import Group


class ClashYAML:
    def __init__(self):
        self._rule = Rule()
        # refersh node list every 60s

    def complete_config(self, groups: Dict[str, Group], ur: UserRequest):
        clash_cfg = copy.deepcopy(CONFIG_TEMPLATE)
        clash_cfg['secret'] = shortuuid.uuid()
        if ur.use_dns:
            clash_cfg['dns'] = DEFAULT_DNS

        # for group entry
        for key, gp in groups.items():
            # `key` is the nickname of groups (such as gfw and acceleration)
            gp_entry = gp.clash_group(ur.use_provider)
            if key == 'gfw' and ur.simple:
                gp_entry['type'] = 'fallback'
                gp_entry['url'] = HEALTH_CHECK_CFGS['gfw']['url']
                gp_entry['interval'] = 600
            clash_cfg['proxy-groups'].append(gp_entry)

        if ur.use_provider:
            # for provider entry
            for key in set(PROVIDER_GROUPS) & set(groups):
                clash_cfg['proxy-providers'][f'provider-{key}'] = (pvd_entry := {
                    'type': 'http',
                    'url': ur.user.provider(ur.provider_args(key)),
                    'path': f'./provider-{key}.yaml',
                    'interval': cfg["subs"]["provider_interval" if key != 'info' else 'info_interval'],
                })
                if key in HEALTH_CHECK_CFGS:
                    pvd_entry['health-check'] = HEALTH_CHECK_CFGS[key]
        else:
            clash_cfg['proxies'] = self._proxy_union(groups)

        clash_cfg['proxy-groups'].sort(key=lambda x: [GROUPS[name] for name in GROUP_ORDER].index(x['name']))

        rule_yaml = self._rule.rule_yaml(ur.is_gfw, ur.client, simple=ur.simple)
        config_yaml = yaml.dump(clash_cfg, Dumper=Dumper, default_flow_style=False)
        final_yaml = config_yaml + '\n' + rule_yaml
        return final_yaml

    def __call__(self, ur: UserRequest) -> Tuple[str, str]:
        """
        Obtain the complete configuration for a certain user. May depend on the host.
        If group is specified, only this group will be returned.
        """
        groups = self._get_proxy(ur)
        if ur.group is not None:
            return f'provider-{ur.group}.yaml', groups.get(ur.group, Group('', [])).provider_return()
        else:
            return 'WallessPKU.yaml', self.complete_config(groups, ur)

    def _get_proxy(self, ur: UserRequest) -> Dict[str, Group]:
        groups = {'gfw': Group(name=GROUPS['gfw'], nodes=[], key='gfw')}
        for node in node_pool.all_nodes(True):
            if node.hidden:
                continue
            for pn in gen_proxy_nodes(node, ur):
                groups['gfw'].nodes.append(pn)
        groups['gfw'].cluster_nodes(ur)

        # adjust groups based on traffic direction and user type
        if ur.show_info:
            groups['info'] = Group(name=GROUPS['info'], nodes=[], key='info')
            groups['info'].nodes = [InfoNode(line) for line in self._get_push_msg(ur.user)]
        
        if ur.is_gfw and not ur.simple:
            groups['acceleration'] = Group(
                name=GROUPS['acceleration'], key='acceleration',
                nodes=[direct_node, groups['gfw']]
            )

        return groups

    @staticmethod
    def _proxy_union(groups: Dict[str, Group]):
        proxies = list()
        added = set()
        for node in groups['gfw'].nodes:
            if isinstance(node, ProxyNode):
                if node.name not in added:
                    proxies.append(node.clash())
                    added.add(node.name)
        return proxies

    # time sensitive LRU cache. It updates every 60 seconds
    @lru_cache(maxsize=1)
    def push_lines(self, _):
        push = Push.objects.order_by('-dt')
        push = push.first()
        if push is None:
            return []
        return [line.replace('\r', '') for line in push.lines.split('\n')]

    def _get_push_msg(self, user):
        lines = deepcopy(self.push_lines(int(time.time())//60))
        if user.balance < 1024:
            lines.insert(0, 'Data is used up! Refill tonight.')
        else:
            lines.insert(0, 'Balance: {}'.format(data_format(user.balance, decimal=True)))
        return lines
