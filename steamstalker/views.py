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

    # Apply the filters.
    # FIXME: Everything below this up until the ``render`` really ought to be
    #        pulled out & placed into the ``Manager``, for better isolation
    #        (and shorter methods).
    seen_qs = profile.friends_seen.filter(created__range=[start_date, end_date]).select_related(depth=1)

    # Aggregate all the data. We'll try to be efficient by only hitting the DB
    # once to fetch everything, then processing through to flesh out the data.
    friends_data = {
        'all_friends': SortedDict(),
        'per_friend': {},
        'per_game': {},
        'max_friends_online': 0,
        'max_friends_ingame': 0,
    }

    # TODO: In thinking about this after the fact, I'm going about generating
    #       timeseries data an inefficient way here. I was leaning on the fact
    #       that the ``offline`` records would help me fill the gaps between
    #       activity, but that breaks down in other ways, like the game graphs.
    #       This stemmed from the original data model.
    #       The solution, I think, is to attack it from the other direction.
    #       Start with a ``datetime``, then just loop over the range
    #       (incrementing by 5 minutes). Look through the records we already
    #       pulled from the DB & anything between the last offset & the current
    #       "top" of the range gets grouped it.
    #       This would ensure that there's correct timeseries data for all the
    #       different metrics & we'd no longer need to store "empties".
    #       For now, it stays because I'm out of time & it (mostly) works.
    for friend_seen in seen_qs:
        # Round down to the nearest 5 minutes, since we're trying not to abuse
        # Steam by hitting it more frequently than that.
        # There's also subtly different ``FriendSeen.created`` times.
        nearest_five = int(friend_seen.created.minute / 5) * 5
        nearest_time = timezone.make_aware(datetime.datetime(
            friend_seen.created.year,
            friend_seen.created.month,
            friend_seen.created.day,
            friend_seen.created.hour,
            nearest_five,
            0), friend_seen.created.tzinfo)
        # d3.js wants Unix timestamps. Painfully make them.
        nearest_timestamp = time.mktime(nearest_time.timetuple())

        # All friends first.
        friends_data['all_friends'].setdefault(nearest_timestamp, {
            'timestamp': nearest_timestamp,
            'ingame': [],
            'online': [],
        })

        if friend_seen.status in ('online', 'ingame'):
            friends_data['all_friends'][nearest_timestamp][friend_seen.status].append(friend_seen.to_friend.username)

        # Then friend-specific bits.
        friends_data['per_friend'].setdefault(friend_seen.to_friend.username, [])
        friend_specific = {
            'username': friend_seen.to_friend.username,
            'current_name': friend_seen.current_name,
            'status': friend_seen.status,
            'timestamp': nearest_timestamp,
        }

        if friend_seen.game:
            friend_specific['game'] = friend_seen.game.name

        friends_data['per_friend'][friend_seen.to_friend.username].append(friend_specific)

        # Last, let's do some game-specific stats.
        if friend_seen.game:
            friends_data['per_game'].setdefault(friend_seen.game.name, SortedDict())
            friends_data['per_game'][friend_seen.game.name].setdefault(nearest_timestamp, [])
            friends_data['per_game'][friend_seen.game.name][nearest_timestamp].append(friend_seen.to_friend.username)

    # Ugly, but now that they're sorted right & grouped, just return lists so
    # d3 is happy.
    friends_data['all_friends'] = friends_data['all_friends'].values()

    for game, time_series_data in friends_data['per_game'].copy().items():
        friends_data['per_game'][game] = [{'timestamp': timestamp, 'usernames': users} for timestamp, users in time_series_data.items()]

    # Calculate some final overall statistics.
    # Tons of room for optimization here, but time is short.
    friends_data['max_friends_online'] = max([len(the_data['online']) for the_data in friends_data['all_friends']])
    friends_data['max_friends_ingame'] = max([len(the_data['online']) + len(the_data['ingame']) for the_data in friends_data['all_friends']])

    return render(request, 'steamstalker/steamprofile_detail.html', {
        'start_date': start_date,
        'end_date': end_date,
        'friends_seen_json': simplejson.dumps(friends_data),
        'username': username,
    })