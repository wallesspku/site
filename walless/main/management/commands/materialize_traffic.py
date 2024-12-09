from django.core.management.base import BaseCommand
from datetime import date, datetime, timedelta, timezone
import os
from collections import defaultdict
import logging
from main.models import User, Traffic, UserTraffic, NodeTraffic
import time
from walless_utils import setup_everything

logger = logging.getLogger('walless')


class Command(BaseCommand):
    help = 'Materialize traffic to refresh the user_traffic and node_traffic tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retrospective', type=int, default=30, 
            help='Number of days to retrospectively materialize'
        )
    
    @staticmethod
    def do_day(day: date):
        # target can be user or node
        if NodeTraffic.objects.filter(ut_date=day).exists():
            # if any exist, we assume all exist
            return False
        traffics = Traffic.objects.filter(ut_date=day)
        if not traffics.exists():
            return False
        node_counts = defaultdict(lambda: [0, 0])
        user_counts = defaultdict(lambda: [0, 0])
        for tra in traffics:
            node_counts[tra.node_id][0] += tra.upload
            node_counts[tra.node_id][1] += tra.download
            user_counts[tra.user_id][0] += tra.upload
            user_counts[tra.user_id][1] += tra.download
        new_user_objects = []
        new_node_objects = []
        for user_id, (upload, download) in user_counts.items():
            new_user_objects.append(UserTraffic(ut_date=day, user_id=user_id, upload=upload, download=download))
        for node_id, (upload, download) in node_counts.items():
            new_node_objects.append(NodeTraffic(ut_date=day, node_id=node_id, upload=upload, download=download))
        UserTraffic.objects.bulk_create(new_user_objects)
        NodeTraffic.objects.bulk_create(new_node_objects)
        return True
    
    def handle(self, retrospective, **kwargs):
        setup_everything(log_paths=[os.path.expanduser('~/.var/log/walless_cron.log')])
        yesterday = datetime.now(tz=timezone(offset=timedelta(hours=8))).date() - timedelta(days=1)
        day = yesterday - timedelta(days=retrospective)
        while day <= yesterday:
            since = time.time()
            if self.do_day(day):
                logger.warning(f'Materialized {day}. Took %.2f seconds' % (time.time() - since))
            day += timedelta(days=1)
        logger.warning('Materialize traffic done')