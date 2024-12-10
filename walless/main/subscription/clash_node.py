from typing import List, Tuple, Dict, Any
import logging
from dataclasses import dataclass

from walless_utils import Node

from ..constants import *
from .user_request import UserRequest
from walless_utils import cfg

logger = logging.getLogger('walless')


class LogicNode:
    """
    Logic node can be:
    1. An actual proxy server, with inbound/outbound on the same node
    note that the v4/v6 ingresses are treated as 2 logic nodes
    2. A relay server, with inbound on one node and outbound on another node
    3. A sentinel node, which is either direct or reject. It does not proxy any traffic
    4. An info node, which is a node that provides information about the subscription
    5. A group can also be a node. it routes the traffic to the nodes in the group
    useful for clash config
    """
    name: str

    def clash(self):
        # return clash config entry
        raise NotImplementedError

    def sort_keys(self):
        return (0,)

    def __lt__(self, other):
        return self.sort_keys() < other.sort_keys()


class SentinelNode(LogicNode):
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


class InfoNode(LogicNode):
    def __init__(self, name: str):
        self.name = name

    def clash(self):
        return dict(type='socks5', name=self.name, server='127.0.0.1', port=10086)

    def __repr__(self):
        return f'<InfoNode {self.name[:10]}>'


@dataclass
class ProxyNode(LogicNode):
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
    # by default, it is node_id
    node_order: int = None
    # node weight = node traffic plan per month. by default it is set to 2000 (GiB)
    # it is used to sample nodes for each cluster
    node_weight: int = 2000

    def __post_init__(self):
        if self.node_order is None:
            self.node_order = self.node_id
        self.additional_config = dict()

    def clash(self) -> Dict[str, Any]:
        ret = {'name': self.name, 'type': 'http', 'port': self.port, 'server': self.server, 'tls': True}
        ret.update({'username': 'walless', 'password': self.uuid, 'sni': cfg['subs'].get('tls_servername')})
        return ret

    def sort_keys(self):
        return (self.ip_protocol, -self.priority, self.node_order)

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
    """
    Collect all possile proxy nodes from a "node" object in the database,
    include v4, v6 (if available), and relay nodes.
    """
    priority = int('good' in node.properties)
    ret = list()

    # direct
    for ip_protocol in [4, 6]:
        if node.can_be_used_by(ur.user.tag, ip_protocol):
            if ur.mix and ip_protocol == 4:
                url = node.urls(ip_protocol)
            else:
                url = node.real_urls(ip_protocol)
            ret.append(pn := ProxyNode(
                name=_rename_server(node.name, node.weight, ip_protocol),
                port=node.port, server=url, priority=priority, ip_protocol=ip_protocol,
                tag=node.tag, uuid=ur.user.uuid, node_id=node.node_id, db_name=node.name,
            ))
            if isinstance(node.traffic_limit, int):
                pn.node_weight = node.traffic_limit

    # relay
    for relay in node.relay_out:
        if not relay.can_be_used_by(ur.user.tag):
            continue
        ret.append(ProxyNode(
            name=_rename_server(relay.name, relay.target.weight, 4),
            port=relay.port, server=relay.source.urls(4), priority=priority, ip_protocol=4,
            tag=relay.tag, uuid=ur.user.uuid, node_id=relay.relay_id, db_name=relay.name,
            node_order=(relay.target.node_id + 0.5)
        ))
    return ret
