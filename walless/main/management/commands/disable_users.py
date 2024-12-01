from django.core.management.base import BaseCommand
import logging
from main.models import User
import time
from walless_utils import setup_everything

logger = logging.getLogger('walless')


class Command(BaseCommand):
    help = 'Disable inactive user'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=180)
        parser.add_argument('--limit', type=int, default=100)
    
    def handle(self, days: int, limit: int, **kwargs):
        setup_everything()
        n_disabled = 0
        thre = int(time.time()) - days * 86400
        for user in User.objects.filter(enabled=True):
            if user.last_activity < thre and user.reg_time < thre:
                user.enabled = False
                user.last_change = int(time.time())
                logger.warning(f'Disabling user {user}')
                user.save()
                n_disabled += 1
            if n_disabled == limit:
                break
