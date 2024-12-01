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
    
    def handle(self, days: int, **kwargs):
        setup_everything()
        max_to_disable = 100
        n_disabled = 0
        thre = int(time.time()) - days * 86400
        for user in User.objects.filter(enabled=True):
            if user.last_activity < thre:
                user.enabled = False
                logger.warning(f'Disabling user {user}')
                user.save()
                n_disabled += 1
            if n_disabled == max_to_disable:
                break
