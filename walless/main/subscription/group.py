from typing import *
import re
from dataclasses import dataclass
import yaml
from collections import defaultdict

from .clash_node import ClashNode, ProxyNode, InfoNode
from ..util import Dumper
from ..constants import PROVIDER_GROUPS, HEALTH_CHECK_CFGS
from .user_request import UserRequest

node_pattern = re.compile(r'([A-Z]{2}-[A-Za-z]+)(\d+)')


@dataclass
class Group(ClashNode):
    # group can also be used as clash node
    name: str
    nodes: List[ClashNode]
    key: str | None = None
    select_type: str = 'select'

    def provider_return(self):
        # return as a provider sub
        if self.nodes:
            entries = [node.clash() for node in self.nodes if isinstance(node, ProxyNode) or isinstance(node, InfoNode)]
        else:
            entries = [{'type': 'socks5', 'name': 'disabled', 'server': 'localhost', 'port': 1}]
        return yaml.dump({'proxies': entries}, Dumper=Dumper, default_flow_style=False)

    # behavior as a node
    def clash(self):
        return self.name

    def __repr__(self):
        return f'<Group {self.name}, {len(self.nodes)} nodes>'

    def clash_group(self, use_provider):
        if not use_provider:
            proxies = [node.name for node in self.nodes]
        else:
            proxies = [node.name for node in self.nodes if not (isinstance(node, ProxyNode) or isinstance(node, InfoNode))]
        entry = {
            'name': self.name,
            'type': self.select_type,
            'proxies': proxies,
        }
        if use_provider and self.key in PROVIDER_GROUPS:
            entry['use'] = [f'provider-{self.key}']
        else:
            if self.key in HEALTH_CHECK_CFGS:
                entry['url'] = HEALTH_CHECK_CFGS[self.key]['url']
        return entry
    
    def cluster_nodes(self, ur: UserRequest):
        if not ur.use_cluster:
            return self
        nodes = []
        # the clustering is name based
        clusters = defaultdict(list)
        for node in self.nodes:
            fetched = node_pattern.findall(node.name)
            if not fetched or not isinstance(node, ProxyNode):
                nodes.append(node)
                continue
            else:
                key = (fetched[0][0], node.ip_protocol)
                clusters[key].append(node)

        for key, cluster in clusters.items():
            cluster.sort()
            # TODO: make this configurable
            ur.rng.shuffle(cluster)
            to_keep = 2
            new_nodes = cluster[:to_keep]
            node_orders = sorted([n.node_order for n in new_nodes])
            for i, node in enumerate(new_nodes):
                old_i = node_pattern.findall(node.name)[0][1]
                node.name = node.name.replace(f'{key[0]}{old_i}', f'{key[0]}{i+1}')
                node.node_order = node_orders[i]
            nodes.extend(new_nodes)

        nodes.sort()
        self.nodes = nodes
