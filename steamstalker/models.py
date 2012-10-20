import bleach
import datetime
from pyquery import PyQuery as pq
import re
import requests
import time
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone


STATUS_CHOICES = [
    ['unknown', 'Unknown'],
    ['offline', 'Offline'],
    ['online', 'Online'],
    ['ingame', 'In-Game'],
]


class Game(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True, blank=True)
    created = models.DateTimeField(editable=False, default=timezone.now)
    updated = models.DateTimeField(editable=False, default=timezone.now)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        self.updated = timezone.now()
        return super(Game, self).save(*args, **kwargs)


class SteamProfile(models.Model):
    username = models.CharField(max_length=128, unique=True, help_text='Your Steam username', db_index=True)
    avatar_url = models.URLField(blank=True, default='')
    import_me = models.BooleanField(default=False, db_index=True)
    last_import = models.DateTimeField(null=True, blank=True, db_index=True)
    created = models.DateTimeField(editable=False, default=timezone.now)
    updated = models.DateTimeField(editable=False, default=timezone.now)

    STEAM_ID_URL = u'http://steamcommunity.com/id/'
    STEAM_PROFILE_URL = u'http://steamcommunity.com/profiles/'
    TIMEOUT = 10

    def __unicode__(self):
        return self.username

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        return super(SteamProfile, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('steamprofile_detail', [], {
            'username': self.username,
        })

    def build_friends_url(self):
        return ''.join([self.STEAM_ID_URL, self.username, '/friends'])

    def parse_username_from_url(self, url):
        if 'profiles/' in url:
            return url.replace(self.STEAM_PROFILE_URL, '')

        return url.replace(self.STEAM_ID_URL, '')

    def fetch_friends(self):
        url = self.build_friends_url()
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:16.0) Gecko/20100101 Firefox/16.0',
            'X-Sorry': 'I wish you had a public API.',
        }

        try:
            resp = requests.get(url, timeout=self.TIMEOUT, headers=headers)
        except requests.models.ConnectionError as e:
            # TODO: Add logging.
            print u'ConnectionError: %s' % e
            return '<html></html>'
        except requests.models.Timeout as e:
            # TODO: Add logging.
            print u'Timeout: %s' % e
            return '<html></html>'

        # Raising an exception (and/or distinquishing between response codes)
        # might be helpful here.
        if resp.status_code != 200:
            print u'Status code: %s' % resp.status_code
            return '<html></html>'

        return resp.content

    def extract_friend(self, friend_elem, friend_type='in-game'):
        friend_data = {
            'url': friend_elem.find('a.linkFriend_{0}'.format(friend_type)).attr('href'),
            'current_name': friend_elem.find('a.linkFriend_{0}'.format(friend_type)).text(),
            'avatar': friend_elem.find('.avatarIcon img').attr('src'),
            'status': 'unknown',
        }
        friend_data['username'] = self.parse_username_from_url(friend_data['url'])

        # What follows hurts. Hooray for scraping!
        raw_status_html = friend_elem.find('.friendSmallText').html()
        raw_status = re.sub('<br/>', ' ', raw_status_html)
        clean_status = bleach.clean(raw_status, strip=True)
        tagless_status = re.sub('\s+', ' ', clean_status)
        friend_status = tagless_status.strip()

        if friend_status in ('', ' ') or friend_status.startswith('Last') or friend_status.startswith('Friends'):
            friend_data['status'] = 'offline'
        elif friend_status.startswith('Online'):
            friend_data['status'] = 'online'
        elif friend_status.startswith('In'):
            friend_data['status'] = 'ingame'

            # Get the game name as well.
            friend_data['game'] = bleach.delinkify(friend_status.replace('In-Game', '').strip())

        return friend_data

    def get_friends_data(self):
        content = self.fetch_friends()

        doc = pq(content)
        friends = []

        for friend_elem in doc('#memberList .friendBlock_in-game'):
            friend_elem = pq(friend_elem)
            friends.append(self.extract_friend(friend_elem, 'in-game'))

        for friend_elem in doc('#memberList .friendBlock_online'):
            friend_elem = pq(friend_elem)
            friends.append(self.extract_friend(friend_elem, 'online'))

        for friend_elem in doc('#memberList .friendBlock_offline'):
            friend_elem = pq(friend_elem)
            friends.append(self.extract_friend(friend_elem, 'offline'))

        return friends

    def get_latest_data(self, imported_at=None):
        friends = self.get_friends_data()

        if imported_at is None:
            imported_at = timezone.now()

        # Fetch all the friends at once to save on DB lookups.
        all_friends = dict([[friend.to_friend.username, friend.to_friend] for friend in self.to_friends.all().select_related(depth=1)])

        for friend_data in friends:
            if friend_data['username'] not in all_friends:
                friend, created = SteamProfile.objects.get_or_create(
                    username=friend_data['username']
                )

                if created:
                    steam_friend = SteamFriend.objects.create(
                        from_friend=self,
                        to_friend=friend
                    )
            else:
                friend = all_friends[friend_data['username']]

            if friend.avatar_url != friend_data.get('avatar', ''):
                friend.avatar_url = friend_data.get('avatar', '')
                friend.save()

            game = None

            if friend_data.get('game', ''):
                game, created = Game.objects.get_or_create(
                    name=friend_data['game']
                )

            if friend_data['status'] in ('online', 'ingame'):
                # We only want to create a record if there's something
                # interesting going on (they're online or in-game). And we
                # only want to create it *ONCE* per-import, even if multiple
                # people have the same friend.
                seen, created = ProfileSeen.objects.get_or_create(
                    seen=friend,
                    created=imported_at,
                    defaults={
                        'status': friend_data['status'],
                        'game': game,
                    }
                )

        self.last_import = imported_at
        self.save()
        return True

    def aggregate_all_friends(self, mini_seen, current_timestamp):
        all_friends_data = {
            'timestamp': current_timestamp,
            'ingame': set(),
            'online': set(),
        }

        for friend_seen in mini_seen:
            if friend_seen.status in ('online', 'ingame'):
                all_friends_data[friend_seen.status].add(friend_seen.seen.username)

        # Convert back to lists for simplejson's benefit.
        all_friends_data['ingame'] = list(all_friends_data['ingame'])
        all_friends_data['online'] = list(all_friends_data['online'])
        return all_friends_data

    def aggregate_per_friend(self, mini_seen, current_timestamp):
        per_friend_data = {}

        for friend_seen in mini_seen:
            per_friend_data[friend_seen.seen.username] = {
                'current_name': friend_seen.current_name,
                'status': friend_seen.status,
            }

        return per_friend_data

    def aggregate_per_game(self, mini_seen, current_timestamp):
        per_game_data = {}

        for friend_seen in mini_seen:
            if friend_seen.game:
                per_game_data.setdefault(friend_seen.game.name, [])
                per_game_data[friend_seen.game.name].append(friend_seen.seen.username)

        return per_game_data

    def friends_data(self, start_date, end_date, increment_by=None):
        the_delta = end_date - start_date
        # Enough to handle 250+ active-at-all-times friends
        amount_to_load = (abs(the_delta.days) + 1) * 100000

        if increment_by is None:
            increment_by = datetime.timedelta(minutes=5)

        # Load these once, so we can cache & reuse them.
        all_friends = self.to_friends.all().select_related(depth=1)

        # Only statuses for your friends.
        friends_seen = ProfileSeen.objects.filter(seen__in=all_friends)
        # Slice it so we fetch them all at once.
        seen_qs = friends_seen.filter(created__range=[start_date, end_date]).select_related(depth=1).order_by('created')[:amount_to_load]
        seen_offset = 0

        all_games = Game.objects.filter(friends_seen__in=friends_seen).values_list('name', flat=True).distinct()

        # Aggregate all the data. We'll try to be efficient by only hitting the DB
        # once to fetch everything, then processing through to flesh out the data.
        friends_data = {
            'all_friends': [],
            'per_friend': {},
            'per_game': {},
        }

        for friend_seen in all_friends:
            friends_data['per_friend'].setdefault(friend_seen.to_friend.username, [])

        for game in all_games:
            friends_data['per_game'].setdefault(game, [])

        default_tz = timezone.get_default_timezone()
        current_date = timezone.make_naive(start_date, default_tz)
        end_date = timezone.make_naive(end_date, default_tz)

        while current_date <= end_date:
            mini_end_date = current_date + increment_by
            current_timestamp = time.mktime(current_date.timetuple())
            # Figure out the statuses in the current timeframe.
            current_seen = [seen for seen in seen_qs if current_date <= timezone.make_naive(seen.created, default_tz) < mini_end_date]

            # ALl friends.
            friends_data['all_friends'].append([
                current_timestamp, self.aggregate_all_friends(current_seen, current_timestamp)
            ])

            # Per-friend.
            per_friend = self.aggregate_per_friend(current_seen, current_timestamp)

            for profile in all_friends:
                if profile.to_friend.username in per_friend:
                    friends_data['per_friend'][profile.to_friend.username].append([
                        current_timestamp, per_friend[profile.to_friend.username]
                    ])
                else:
                    friends_data['per_friend'][profile.to_friend.username].append([
                        current_timestamp, {'status': 'offline'}
                    ])

            # Per-game.
            per_game = self.aggregate_per_game(current_seen, current_timestamp)

            for game in all_games:
                if game in per_game:
                    friends_data['per_game'][game].append([
                        current_timestamp, per_game[game]
                    ])
                else:
                    friends_data['per_game'][game].append([
                        current_timestamp, []
                    ])

            current_date = mini_end_date

        return friends_data


class SteamFriend(models.Model):
    """
    Just the relationship component, showing who is friends with who.
    """
    from_friend = models.ForeignKey(SteamProfile, related_name='to_friends')
    to_friend = models.ForeignKey(SteamProfile, related_name='from_friends')
    created = models.DateTimeField(editable=False, default=timezone.now)
    updated = models.DateTimeField(editable=False, default=timezone.now)

    def __unicode__(self):
        return u"{0} to {1}".format(self.from_friend.username, self.to_friend.username)

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        return super(SteamFriend, self).save(*args, **kwargs)


class ProfileSeen(models.Model):
    """
    An activity indicator, showing someone is online or in-game.
    """
    seen = models.ForeignKey(SteamProfile, related_name='seen')
    current_name = models.CharField(max_length=128, default='', blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='online', db_index=True)
    game = models.ForeignKey(Game, related_name='friends_seen', null=True, blank=True)
    created = models.DateTimeField(editable=False, default=timezone.now)

    def __unicode__(self):
        return u"{0} ({1})".format(self.seen.username, self.status)
