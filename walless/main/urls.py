from django.urls import path

from .register.pages import verify_page, direct_register, verify_result_page, reset_user_page
from .subscription.pages import clash_sub_page
from .user.pages import profile
from .util import ping_page


urlpatterns = [
    path('', verify_page),
    path('ping', ping_page),
    # user space
    path('verify', verify_page),
    path('verify/', verify_result_page),
    path('profile/<str:email>/<str:password>', profile),
    path('clash/<str:email>/<str:password>', clash_sub_page),
    path('reset/<str:email>/<str:password>', reset_user_page),

    # admin space
    path('a/force/<str:email>', direct_register),
]
