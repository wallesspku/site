import time
import logging
from threading import Semaphore

from django.http import Http404, HttpResponse
from walless_utils import db, EditReservior, user_pool

from .clash_yaml import ClashYAML
from ..util import get_client_ip, next_refresh, setup_globals
from .user_request import UserRequest

yaml_gen = ClashYAML()
sublog_cache = EditReservior(
    sql=db.insert_sublog_sql, db=db, cache_size=1024, cache_time=300,
)
TIME_WARNING = 2.5
logger = logging.getLogger('walless')
sub_semaphore = Semaphore(64)


def clash_sub_page(request, email, password):
    try:
        if not sub_semaphore.acquire(blocking=False):
            logger.warning(f'Too busy. Abort {email}.')
            raise Http404('Too busy.')
        return _clash_sub_page(request, email, password)
    finally:
        sub_semaphore.release()


def _clash_sub_page(request, email, password):
    setup_globals()
    since = time.time()
    # verify the user identity
    user_pool.pull()
    if email not in user_pool.email2user:
        logger.info(f'{email} not found. Try to pull this single user.')
        user_pool.pull_one_user(email)
        if email not in user_pool.email2user:
            logger.warning(f'{email} asked for subs, but email is not found!')
            raise Http404('Email not found!')
    user_obj = user_pool.email2user.get(email)
    if user_obj is None or user_obj.password != password:
        logger.warning(f'{email} asked for subs, but password does not match!')
        raise Http404('Password is wrong.')
    if not user_obj.enabled:
        logger.warning(f'{email} asked for subs, but it is disabled. Re-enable it.')
        db.enable_user(user_obj.user_id, True)
    time_verify = time.time() - since
    since = time.time()

    # parse the user agent and parameters; ur contains everything that is user related.
    ur = UserRequest.from_request(request, user_obj)
    sublog_cache.add((
        int(time.time()),
        get_client_ip(request),
        f'{ur.client}/{ur.client_version}',
        ur.group, 
        user_obj.user_id)
    )
    time_sublog = time.time() - since
    since = time.time()

    file_name, sub = yaml_gen(ur)
    response = HttpResponse(sub, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={file_name}'
    response['profile-update-interval'] = 12
    response['subscription-userinfo'] = f'upload=0; download={user_obj.total_data-user_obj.balance}; ' \
        f'total={user_obj.total_data}; expire={next_refresh()}'

    time_yaml= time.time() - since
    time_total = (time_verify + time_sublog + time_yaml)
    if time_total > TIME_WARNING:
        logger.warning(
            f'Used {time_total:.2f}s for the subs of {email}. '
            f'{time_verify=:.2f}, {time_sublog=:.2f}, {time_yaml=:.2f}.'
        )

    return response
