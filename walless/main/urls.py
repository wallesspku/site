from django.urls import path
import os
import logging

from .register.pages import verify_page, direct_register, verify_result_page, reset_user_page
from .subscription.pages import clash_sub_page
from .user.pages import profile
from .util import ping_page

logger = logging.getLogger('walless')


urlpatterns = [
    path('ping', ping_page),
    # user space
    path('profile/<str:email>/<str:password>', profile),
    path('clash/<str:email>/<str:password>', clash_sub_page),
]

if os.environ.get('MAIN_SUBS_SERVER', '0') == '1':
    # Only one server can do these!
    logger.warning("Consider this node as the main subs server.")
    urlpatterns.extend([
        path('', verify_page),
        path('verify', verify_page),
        path('verify/', verify_result_page),
        path('reset/<str:email>/<str:password>', reset_user_page),
        path('a/force/<str:email>', direct_register),
    ])
