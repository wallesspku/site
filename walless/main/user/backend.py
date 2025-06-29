from copy import deepcopy
import logging
import datetime

from django.http import Http404
from walless_utils import db, data_format, user_pool

from ..util import current_time

logger = logging.getLogger('walless')


def profile_info(email, password):
    user_pool.pull()
    user_obj = user_pool.email2user.get(email)
    if user_obj is None or user_obj.password != password:
        logger.error(f'User {email} not found, or password not matched.')
        raise Http404
    if not user_obj.valid:
        raise Http404('User is not valid.')
    user_obj = deepcopy(user_obj)

    user_obj.percentage = 100 - (int(user_obj.balance)) * 100 // user_obj.total_data
    user_obj.total_data_formatted = data_format(user_obj.download + user_obj.upload)
    user_obj.upload, user_obj.download = data_format(user_obj.upload), data_format(user_obj.download)
    user_obj.balance = data_format(user_obj.balance, decimal=True)

    if user_obj.register_day == datetime.datetime(year=2017, month=1, day=1).date():
        user_obj.register_day = 'Not recorded'

    user_obj.total_quota = data_format(user_obj.total_data, decimal=True)
    user_obj.data_per_day = data_format(user_obj.daily_data, decimal=True)

    sort_by_date = dict()

    time_limit = current_time().date() - datetime.timedelta(days=30)
    activities = db.get_traffic_after(user_obj.user_id, time_limit)
    for act in activities:
        act_date = act.date
        if act_date not in sort_by_date:
            sort_by_date[act_date] = [0, 0]
        sort_by_date[act_date][0] += act.upload
        sort_by_date[act_date][1] += act.download

    sort_by_date = sorted(list(sort_by_date.items()), key=lambda sbd: sbd[0], reverse=True)

    user_obj.activities = list()

    class Dummy:
        pass
    for date, [upload, download] in sort_by_date:
        sbd_obj = Dummy()
        sbd_obj.date = str(date)
        sbd_obj.total = data_format(upload + download)
        sbd_obj.upload = data_format(upload)
        sbd_obj.download = data_format(download)
        user_obj.activities.append(sbd_obj)

    dict_data = vars(user_obj).copy()
    dict_data['clash_sub_url'] = user_obj.clash_sub_url

    return dict_data
