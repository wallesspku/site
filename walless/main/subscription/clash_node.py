from typing import *
import logging
from dataclasses import dataclass

from walless_utils import Node

from ..constants import *
from .user_request import UserRequest
from walless_utils import cfg

logger = logging.getLogger('walless')


class ClashNode:
    name: str

    # an entry in clash
    def clash(self):
        raise NotImplementedError

    def sort_keys(self):
        return (0,)

    def __lt__(self, other):
        return self.sort_keys() < other.sort_keys()


class SentinelNode(ClashNode):
    # for direct and reject
    def __init__(self, name: str):
        self.name = name

    def clash(self):
        return self.name

    def sort_keys(self):
        return (self.name == 'DIRECT',)

    def __repr__(self):
        return f'<SentinelNode {self.name}>'


direct_node, reject_node = SentinelNode('DIRECT'), SentinelNode('REJECT')


class InfoNode(ClashNode):
    def __init__(self, name: str):
        self.name = name

    def clash(self):
        return dict(type='socks5', name=self.name, server='127.0.0.1', port=10086)

    def __repr__(self):
        return f'<InfoNode {self.name[:10]}>'


@dataclass
class ProxyNode(ClashNode):
    name: str
    port: int
    server: str
    priority: int
    # 4 or 6
    ip_protocol: int
    tag: Tuple[str]
    uuid: str
    node_id: int
    db_name: str
    # additional_args: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.additional_config = dict()

    def clash(self) -> Dict[str, Any]:
        ret = {'name': self.name, 'type': 'http', 'port': self.port, 'server': self.server, 'tls': True}
        ret.update({'username': 'walless', 'password': self.uuid, 'sni': cfg['subs'].get('tls_servername')})
        return ret

    def sort_keys(self):
        return self.ip_protocol, -self.priority, self.node_id,

    def __lt__(self, other):
        return self.sort_keys() < other.sort_keys()

    def __repr__(self):
        return f'<ProxyNode {self.name}>'


def _rename_server(name, weight, ip_protocol: int) -> str:
    flag = ''
    if name[:2] in FLAGS:
        flag = FLAGS[name[:2]]
    if weight == 1.0:
        tags = []
    elif weight < 1e-3:
        tags = ['free']
    else:
        tags = [f'{weight}x']
    if tags:
        name = name + ' (' + ','.join(tags) + ')'
    tags = list()
    if ip_protocol == 6:
        tags.append('v6')
    if len(tags) > 0:
        name = '[' + ','.join(tags) + ']' + name
    return (flag + ' ' + name).strip()


def gen_proxy_nodes(node: Node, ur: UserRequest) -> List[ProxyNode]:
    priority = int('good' in node.tag)
    ret = list()

    # direct
    for ip_protocol in [4, 6]:
        if node.can_be_used_by(ur.user.tag, ip_protocol):
            url = node.urls(ip_protocol) if ur.mix else node.real_urls(ip_protocol)
            ret.append(ProxyNode(
                _rename_server(node.name, node.weight, ip_protocol),
                node.port, url, priority, ip_protocol,
                node.tag, ur.user.uuid, node.node_id, node.name
            ))

    # relay
    for relay in node.relay_out:
        if not relay.can_be_used_by(ur.user.tag):
            continue
        ret.append(ProxyNode(
            _rename_server(relay.name, relay.target.weight, 4),
            relay.port, relay.source.urls(4), priority, 4,
            relay.tag, ur.user.uuid, relay.relay_id, relay.name,
        ))
    return ret
