from django.core.management.base import BaseCommand
import os
import logging
from datetime import timedelta, datetime, timezone
from collections import defaultdict
from main.models import User, Traffic, UserTraffic, NodeTraffic
import time
from walless_utils import setup_everything, db, data_format
from .materialize_traffic import Command as Materialization

reporter = logging.getLogger('sublog')
logger = logging.getLogger('walless')


class Command(BaseCommand):
    help = 'Show daily stats'

    def add_arguments(self, parser):
        pass

    @staticmethod
    def stats_day(day):
        all_users = db.all_users(enable_only=False)
        def users_before(d):
            return len(list(filter(lambda x: x.register_day <= d, all_users)))
        stats = {
            'total_user': users_before(day),
            'new_user': users_before(day) - users_before(day-timedelta(days=1)),
            'total_data': data_format(sum(map(lambda x: x.upload + x.download, all_users)), decimal=True),
            'user_data': list(),
            'node_data': list(),
            'daily_active_user': 0,
            'data': {
                'upload': 0,
                'download': 0,
                'total': 0,
            }
        }
        # Node traffic info
        uuid2node = {node.uuid: node for node in db.all_servers(include_delete=True)}
        for nt in NodeTraffic.objects.filter(ut_date=day):
            stats['node_data'].append([
                uuid2node[nt.node_id].name, data_format(nt.upload+nt.download, decimal=True)
            ])
            stats['data']['upload'] += nt.upload
            stats['data']['download'] += nt.download
        stats['data']['total'] = stats['data']['upload'] + stats['data']['download']
        
        # User traffic info
        user2traffic = dict()
        for ut in UserTraffic.objects.filter(ut_date=day):
            user2traffic[ut.user_id] = ut.upload + ut.download
        def threshold(th, name):
            n = len(list(user2traffic.values()))
            stats['user_data'].append([f'users (>{name})', n])
        threshold(2**20, '1MB')
        threshold(2**27, '128MB')
        threshold(2**30, '1GB')
        stats['daily_active_user'] = len(user2traffic)
        stats['data'] = {k: data_format(v, decimal=True) for k, v in stats['data'].items()}
        return stats
    
    def handle(self, **kwargs):
        setup_everything(log_paths=[os.path.expanduser('~/.var/log/walless_cron.log')])
        from notifier import NotifierHandler
        reporter.addHandler(NotifierHandler())

        yesterday = datetime.now(tz=timezone(offset=timedelta(hours=8))).date() - timedelta(days=1)
        Materialization.do_day(yesterday)

        since = time.time()
        stats = self.stats_day(yesterday)
        logger.warning('Doing daily stats. `stats_one_day` took %.2f seconds' % (time.time() - since))

        to_warn = [
            f'#daily\\_stats of {yesterday}',
            f"total users: {stats['total_user']} ({stats['new_user']} new)",
            f"total data: {stats['total_data']}",
            f"daily active {stats['daily_active_user']}",
            f"traffic {stats['data']['total']} (u={stats['data']['upload']}, d={stats['data']['download']})"
        ]
        for head, n in stats['user_data']:
            to_warn.append(head + ': ' + str(n))
        reporter.warning('\n'.join(to_warn))
        time.sleep(1)
        to_warn = []
        for node_name, n in stats['node_data']:
            to_warn.append(node_name + ': ' + n)
        reporter.warning('\n'.join(to_warn))
