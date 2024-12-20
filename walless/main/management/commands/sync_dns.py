from django.core.management.base import BaseCommand
import os
import logging

from walless_utils import setup_everything, cfg, db
from walless_utils.api.cloudflare import Cloudflare
from walless_utils.api.huawei import Huawei

logger = logging.getLogger('walless')


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
            for scope in ['default', 'edu']:
                if node.ip(4) is None:
                    continue
                if scope in node.mix:
                    db_cname = node.mix[scope].real_urls(4)
                else:
                    db_cname = node.real_urls(4)
                if scope not in node.dns[4].cname or node.dns[4].cname[scope] != db_cname:
                    logger.warning(
                        f'{scope} CNAME for {node.name} is missing. '
                        f'It should be {db_cname}. Modifying it now.'
                    )
                    hw.add_mod_cname(node.urls(4), **{scope+'_cname': db_cname})
