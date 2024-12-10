import os
import copy
import yaml
from functools import lru_cache

from ..constants import GROUPS
from ..util import Dumper


class Rule:
    def __init__(self):
        self._rule_lists = dict()
        self._prepare_rule_list()

    def _prepare_rule_list(self):
        site_categories = {
            category_name: [
                line.replace('\n', '').replace('\r', '')
                for line in open(os.path.join('rules', category_name + '.txt')).readlines()
                if line != '' and '//' not in line and line.count(',') == 1
            ]
            for category_name in map(lambda x: x[:-4], os.listdir('rules'))
        }

        def append_rule(category_group_pairs):
            ret = list()
            for category, group in category_group_pairs:
                ret.extend([line+','+group for line in site_categories[category]])
            return ret

        self._rule_lists['default'] = append_rule([
            ('academics', 'DIRECT'),
            ('gfw', GROUPS['gfw']),
            ('china', 'DIRECT'),
            ('local', 'DIRECT'),
        ])

        self._rule_lists['back'] = append_rule([
            ('local', 'DIRECT'),
            ('back', GROUPS['gfw']),
        ])

        self._rule_lists['pharos'] = append_rule([
            ('china', 'DIRECT'),
            # ('gfw_abridged', GROUPS['gfw']),
            ('noproxy', 'DIRECT'),
            ('local', 'DIRECT'),
        ])

    @lru_cache(128)
    def rule_yaml(self, is_gfw, host, simple):
        rules = self._get_rule_list(is_gfw, host, simple)
        return yaml.dump({'rules': rules}, Dumper=Dumper, default_flow_style=False)

    def _get_rule_list(self, is_gfw, host, simple):
        if not is_gfw:
            # Deal with back user first
            rules = copy.deepcopy(self._rule_lists['back'])
            if host == 'pharos':
                rules.append('MATCH,DIRECT')
            else:
                rules.append('IP-CIDR,0.0.0.0/0,DIRECT')
                rules.append('MATCH,DIRECT')
            return rules

        if host == 'pharos':
            # general pharos users
            rules = copy.deepcopy(self._rule_lists['pharos'])
            rules.append('MATCH,'+GROUPS['gfw'])
            return rules

        # General users
        rules = copy.deepcopy(self._rule_lists['default'])
        if not simple:
            rules.append('IP-CIDR,0.0.0.0/0,'+GROUPS['acceleration'])
        rules.append('MATCH,DIRECT')
        return rules
