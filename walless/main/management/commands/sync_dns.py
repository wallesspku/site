from django.core.management.base import BaseCommand
import os
import logging

from walless_utils import setup_everything, cfg, db, Node
from walless_utils.api.cloudflare import Cloudflare
from walless_utils.api.huawei import Huawei

logger = logging.getLogger('walless')


def cname_match(node: Node):
    cnames = dict()
    for line, cname_records in node.dns[4].cname.items():
        cnames[line] = {rec['records'][0] for rec in cname_records}

    if set(cnames) != set(node.mix):
        return False
    for line, records in cnames.items():
        if set(node_mix_target(node, line)) != records:
            return False
    return True


def node_mix_target(node: Node, line: str):
    if line in node.mix:
        return [tgt.real_urls(4) + '.' for tgt in node.mix[line]]
    return []


class Command(BaseCommand):
    help = 'Sync DNS A, AAAA, and CNAME records'

    def handle(self, **kwargs):
        setup_everything(log_paths=[os.path.expanduser('~/.var/log/walless_cron.log')])
        nodes = db.all_servers(get_mix=True, get_relays=True, include_delete=True)
        cf = Cloudflare()
        cf.apply_nodes(nodes)
        hw = Huawei(cfg['huawei'])
        hw.apply_nodes(nodes)

        # apply the A/AAAA records on DB to cloudflare, if mismatched
        for node in nodes:
            for proto in [4, 6]:
                if node.ip(proto) is not None and node.dns[proto].ip != node.ip(proto):
                    logger.warning(
                        f'The IPv{proto} of {node.name} mismatches. '
                        f'Setting its DNS records to {node.ip(proto)}.'
                    )
                    cf.update_dns(node.real_urls(proto), node.ip(proto))

        # apply the mix settings on DB to huawei cloud, if mismatched
        # only ipv4 (CNAME for A record) will be mapped
        for node in nodes:
            if cname_match(node):
                continue
            logger.warning(f'CNAME for {node.name} mismatches. Fixing it now.')
            # we do not modify records; we delete and recreate them
            for records in node.dns[4].cname.values():
                for rec in records:
                    hw.delete_record(rec['id'])
            for line in node.mix:
                for tgt in node_mix_target(node, line):
                    hw.add_record_set(node.urls(4)+'.', line, tgt)
