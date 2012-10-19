import datetime
from dateutil.parser import parse as dateutil_parse
import requests
import simplejson
import time
from django.shortcuts import render
from django.utils.datastructures import SortedDict
from django.utils import timezone
from .models import SteamProfile


def steamprofile_add(request, username):
    profile_url = '/'.join(['http://steamcommunity.com/id/', username])
    # Assume they don't exist first, unless proved otherwise.
    profile = None
    created = False

    try:
        # Hit up Steam & see if they exist.
        resp = requests.get(profile_url, timeout=10)

        if resp.status_code == 200:
            # They're there. Get/Create a new profile.
            profile, created = SteamProfile.objects.get_or_create(
                username=username
            )
            # Separately, set them to be importable (so we don't try to create
            # a duplicate entry for the above user).
            profile.import_me = True
            profile.save()
    except (requests.models.ConnectionError, requests.models.Timeout):
        # Don't do anything, it's not there.
        pass

    return render(request, 'steamstalker/steamprofile_add.html', {
        'profile': profile,
        'created': created,
        'username': username,
    })


def steamprofile_detail(request, username):
    # See if we've got the profile already.
    try:
        profile = SteamProfile.objects.get(username=username, import_me=True)
    except SteamProfile.DoesNotExist:
        return steamprofile_add(request, username)

    start_date = timezone.now() - datetime.timedelta(days=1)
    end_date = timezone.now()

    if request.GET.get('start_date'):
        start_date = dateutil_parse(request.GET['start_date'])

    if request.GET.get('end_date'):
        end_date = dateutil_parse(request.GET['end_date'])

    if end_date < start_date:
        start_date, end_date = end_date, start_date

    friends_data = profile.friends_data(start_date, end_date)

    return render(request, 'steamstalker/steamprofile_detail.html', {
        'start_date': start_date,
        'end_date': end_date,
        'friends_seen_json': simplejson.dumps(friends_data),
        'username': username,
    })