from django.core.management.base import BaseCommand
import os
import logging

from walless_utils import setup_everything, cfg, db, Node
from walless_utils.api.cloudflare import Cloudflare
from walless_utils.api.huawei import Huawei

logger = logging.getLogger('walless')


def cname_match(node: Node):
    if len(node.mix) == 0:
        # if mix is not set, it should point to itself
        if len(node.dns[4].cname) != 1:
            return False
        return set(node.dns[4].cname['default_view']['records']) == {node.real_urls(4)+'.'}

    # otherwise, check each item individually
    if not set(node.dns[4].cname) != set(node.mix):
        return False
    for line in node.mix:
        if line not in node.dns[4].cname:
            return False
        if set(node_records(node, line)) != set(node.dns[4].cname[line]['records']):
            return False
    return True


def node_records(node: Node, line: str):
    if line in node.mix:
        return [tgt.real_urls(4) + '.' for tgt in node.mix[line]]
    return []


class Command(BaseCommand):
    help = 'Sync DNS A, AAAA, and CNAME records'

    def handle(self, **kwargs):
        setup_everything(log_paths=[os.path.expanduser('~/.var/log/walless_cron.log')])
        nodes = db.all_servers(get_mix=True, get_relays=True, include_delete=False)
        cf = Cloudflare()
        cf.apply_nodes(nodes)
        hw = Huawei(cfg['huawei'])
        hw.apply_nodes(nodes)

        # apply the ipv4/ipv6 records on DB to cloudflare, if mismatched
        for node in nodes:
            for proto in [4, 6]:
                if node.ip(proto) is not None and node.dns[proto].ip != node.ip(proto):
                    logger.warning(
                        f'The IPv{proto} of {node.name} mismatches. '
                        'Setting its DNS records to {node.ip(proto)}.'
                    )
                    cf.update_dns(node.real_urls(proto), node.ip(proto))

        # apply the mix settings on DB to huawei cloud, if mismatched
        # only ipv4 (A record) will be mapped
        for node in nodes:
            if cname_match(node):
                continue
            logger.warning(f'CNAME for {node.name} mismatches. Fixing it now.')
            # we do not modify records; we delete and recreate them
            for content in node.dns[4].cname.values():
                hw.delete_record(content['id'])
            if 'default_view' not in node.mix:
                node.mix['default_view'] = [node]
            for line in node.mix:
                records = node_records(node, line)
                hw.add_record_set(node.urls(4)+'.', line, records)
