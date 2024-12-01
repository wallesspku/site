from typing import *
import re
from dataclasses import dataclass, field
import random

from walless_utils import User, cfg


ua_pat = re.compile(r'(.*?)/(.+?)( |$)', re.IGNORECASE)
client_map = {
    'clashforwindows': 'cfw',
    'clashforandroid': 'cfa',
    'clashx': 'clashx',
    'clashx pro': 'clashx',
    # 'clash': 'choc',
}


@dataclass
class UserRequest:
    user: User = None
    client: str = None
    client_version: str = None
    group: Optional[str] = None
    # if set, return one sampled node from each cluster
    cluster: bool = True
    _dns: bool = False
    _provider: bool = False
    _mix: Optional[bool] = None
    user_provided_params: Dict[str, str] = field(default_factory=dict)

    @property
    def mix(self):
        if self._mix is not None:
            return self._mix
        return set(self.user.tag) == {'c', 'gfw'}

    @property
    def use_clash_core(self) -> bool:
        return self.client in {'cfw', 'cfa', 'clashx'}

    @property
    def use_provider(self) -> bool:
        if self._provider is not None:
            return self._provider
        if not cfg['subs'].get('provider', True):
            return False
        return self.use_clash_core

    @property
    def use_dns(self) -> bool:
        if self._dns is not None:
            return self._dns
        return cfg['subs'].get('use_dns', False)

    @classmethod
    def from_request(cls, request, user: User):
        ur = cls(user)

        if 'HTTP_USER_AGENT' in request.META:
            ua = request.META['HTTP_USER_AGENT']
            matched = ua_pat.findall(ua)
            if len(matched) == 0:
                ur.client, ur.client_version = 'unknown', 'unknown'
            else:
                ur.client, ur.client_version = matched[0][0].lower(), matched[0][1].lower()
                if ur.client in client_map:
                    ur.client = client_map[ur.client]
        else:
            ur.client, ur.client_version = 'unknown', 'unknown'
        
        def parse_flag(key, default=None):
            if key in request.GET:
                ur.user_provided_params[key] = request.GET.get(key)
                return request.GET.get(key) == 'true'
            return default

        ur.client = request.GET.get('client', ur.client)
        ur.client_version = request.GET.get('version', ur.client_version)
        ur._dns = parse_flag('dns')
        ur._provider = parse_flag('provider')
        ur.cluster = parse_flag('cluster', True)
        ur.group = request.GET.get('group', None)
        if ur.group == 'scholar':
            # user may not update their subs file. when they query the scholar group, return gfw instead
            ur.group = 'gfw'
        ur._mix = parse_flag('mix')
        return ur

    def provider_args(self, group: str) -> str:
        additional_args = {'group': group}
        if self.user_provided_params:
            additional_args.update(self.user_provided_params)
        if self.client is not None:
            additional_args['client'] = self.client
        if self.client_version is not None:
            additional_args['version'] = self.client_version
        if additional_args:
            return '?' + '&'.join([f'{k}={v}' for k, v in additional_args.items()])
        else:
            return ''
    
    @property
    def use_cluster(self):
        return self.cluster and not self.simple

    @property
    def client_versions(self) -> Tuple[Union[int, str], ...]:
        ret = self.client_version.split('.')
        for i, item in enumerate(ret.copy()):
            if item.isdigit():
                ret[i] = int(item)
        return tuple(ret)

    @property
    def show_info(self) -> bool:
        # if the info group should be shown
        if not self.use_clash_core:
            return False
        if not self.use_provider:
            return False
        return set(self.user.tag) == {'gfw', 'c'}

    @property
    def is_gfw(self):
        return 'cn' not in self.user.tag
    
    @property
    def simple(self):
        return 'c' not in self.user.tag
    
    @property
    def rng(self):
        return random.Random(hash(self.user.email))
