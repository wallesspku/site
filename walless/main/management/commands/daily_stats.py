from django.core.management.base import BaseCommand
import os
import logging
from datetime import timedelta, datetime, timezone, date
import time

from tabulate import tabulate

from walless_utils import setup_everything, db, data_format, today
from main.models import UserTraffic, NodeTraffic
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
            'monthly_active_user': 0,
            'data': {
                'upload': 0,
                'download': 0,
                'total': 0,
            },
        }
        # Node traffic info
        nodes = db.all_servers(include_delete=True)
        uuid2node = {node.uuid: node for node in nodes}
        for nt in NodeTraffic.objects.filter(ut_date=day):
            stats['node_data'].append([
                uuid2node[nt.node_id].name, nt.upload+nt.download
            ])
            stats['data']['upload'] += nt.upload
            stats['data']['download'] += nt.download
        stats['data']['total'] = stats['data']['upload'] + stats['data']['download']
        stats['node_data'].sort(key=lambda x: x[1], reverse=True)
        stats['node_data'] = [[x[0], data_format(x[1], decimal=True)] for x in stats['node_data']]
        
        # User traffic info
        user2traffic = dict()
        for ut in UserTraffic.objects.filter(ut_date=day):
            user2traffic[ut.user_id] = ut.upload + ut.download
        def threshold(th, name):
            n = len([1 for t in user2traffic.values() if t > th])
            stats['user_data'].append([f'users (>{name})', n])
        threshold(2**20, '1MB')
        threshold(2**27, '128MB')
        threshold(2**30, '1GB')

        def num_active(day: date):
            return len([1 for u in all_users if u.last_active_day >= day])

        stats['daily_active_user'] = num_active(today() - timedelta(days=1))
        stats['monthly_active_user'] = num_active(today() - timedelta(days=30))
        stats['data'] = {k: data_format(v, decimal=True) for k, v in stats['data'].items()}

        # traffic plan       
        node_traffics = list(NodeTraffic.objects.filter(ut_date__gt=today()-timedelta(days=32)))
        stats['plan'] = []
        for node in nodes:
            if node.traffic_limit is None or node.deleted:
                continue
            span = node.next_reset_day() - node.last_reset_day()
            passed = today() - node.last_reset_day()
            time_percentage = round(passed / span * 100)
            traffic = sum([x.upload + x.download for x in node_traffics if x.node_id == node.uuid and x.ut_date >= node.last_reset_day()])
            limit = node.traffic_limit * 1024**3
            traffic_percentage = round(traffic / limit * 100)
            stats['plan'].append([
                node.name, node.idc,
                str(passed.days).ljust(2) + f' {time_percentage}%',
                f'{round(traffic/1024**4, 1)}/{round(limit/1024**4, 1)}'.ljust(9) + f' {traffic_percentage}%'
            ])

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

        lines = [
            ['traffic', stats['data']['total']],
            ['new users', stats['new_user']],
            ['daily active', stats['daily_active_user']],
            ['monthly active', stats['monthly_active_user']],
        ]
        for k, v in stats['user_data']:
            lines.append([k, v])
        lines.extend([
            ['total users', f"{stats['total_user']}"],
            ['total traffic', stats['total_data']],
        ])
        to_warn = f'#daily\\_stats of {yesterday}\n```\n' + tabulate(lines, tablefmt='plain') + '\n```'
        reporter.warning(to_warn)
        time.sleep(1)

        reporter.warning('```\n'+tabulate(stats['node_data'], headers=['Node', 'Traffic'])+'\n```')
        time.sleep(1)

        reporter.warning('```\n'+tabulate(stats['plan'], headers=['Node', 'IDC', 'Days', 'Traffic (TiB)'])+'\n```')
