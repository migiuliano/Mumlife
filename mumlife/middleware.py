# mumlife/middleware.py
import logging
import json
import requests
from django.conf import settings
from django.middleware.csrf import get_token
from mumlife import views

logger = logging.getLogger('mumlife.middleware')


class MumlifeMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        __processed_views = dir(views)
        # make sure this view is not processed,
        # or we'll have ourself an infinite loop
        if request.user.is_authenticated() and view_func.__name__ in __processed_views:
            # Fetch notifications from the API using cookie authentication
            protocol = 'https' if request.is_secure() else 'http'
            url = '{}:{}notifications/'.format(protocol, settings.API_URL)
            cookies = {
                'sessionid': request.COOKIES[settings.SESSION_COOKIE_NAME],
                'csrftoken': request.COOKIES[settings.CSRF_COOKIE_NAME]
            }
            r = requests.get(url, verify=False, cookies=cookies, params={'format': 'json'})
            try:
                response = json.loads(r.text)
                request.META["MUMLIFE_NOTIFICATIONS"] = response
            except ValueError:
                request.META["MUMLIFE_NOTIFICATIONS"] = {}
        return None


def request(request):
    meta = {
        'SITE_URL': settings.SITE_URL,
        'API_URL': settings.API_URL
    }

    if request.user.is_authenticated():
        # Check for new notifications
        account = request.user.get_profile()
        try:
            read = account.notifications.total
        except:
            read = 0
        if request.META.has_key("MUMLIFE_NOTIFICATIONS") and request.META["MUMLIFE_NOTIFICATIONS"]:
            total = request.META["MUMLIFE_NOTIFICATIONS"]['total']
        else:
            total = 0
        unread = total - read
        if unread < 0:
            unread = 0
        meta['new_notifications'] = True if unread else False
    return meta