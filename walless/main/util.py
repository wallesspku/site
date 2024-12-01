import datetime
import logging
import os
import re

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from django.http import HttpResponse
from walless_utils import setup_everything

email_pat = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
logger = logging.getLogger('walless')


def setup_globals():
    log_path = os.path.expanduser('~/.var/log/walless_site.log')
    setup_everything(
        log_paths=[log_path], pull_node=True, pull_user=True, 
        user_pool_kwargs={'enable_only': False}
    )


def current_time():
    tz = datetime.timezone(offset=datetime.timedelta(hours=8))
    return datetime.datetime.now(tz=tz)


def next_refresh() -> int:
    next_day = current_time() + datetime.timedelta(days=1)
    next_day = next_day.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(next_day.timestamp())


def get_client_ip(request):
    ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if ip is None:
        ip = request.META.get('HTTP_X_REAL_IP')
    if ip is None:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ping_page(request):
    setup_globals()
    return HttpResponse('pong')
