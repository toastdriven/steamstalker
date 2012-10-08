import bleach
from pyquery import PyQuery as pq
import re
import requests
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
    import_me = models.BooleanField(default=False)
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

    def get_latest_data(self):
        friends = self.get_friends_data()
        now = timezone.now()

        for friend_data in friends:
            friend, created = SteamProfile.objects.get_or_create(
                username=friend_data['username']
            )

            if friend_data.get('avatar', '') and friend.avatar_url != friend_data.get('avatar', ''):
                friend.avatar_url = friend_data.get('avatar', '')
                friend.save()

            game = None

            if friend_data.get('game', ''):
                game, created = Game.objects.get_or_create(
                    name=friend_data['game']
                )

            seen = FriendSeen.objects.create(
                profile=self,
                to_friend=friend,
                status=friend_data['status'],
                game=game,
                created=now
            )

        self.last_import = timezone.now()
        self.save()
        return True


# TODO: This way of storing the data is pretty inefficient, since it's
#       constantly creating records for offline users (most of them) & because
#       it'll dupe records if two (or more) people have the same friend (who's
#       online status will be the same).
#       Fixing this would involve creating a new model to be *just* the
#       relationship piece, taking the ``profile`` *out* of this model, then
#       using ``get_or_create`` on this model in the import code.
#       For now, it stays because I'm out of time & it works, just space-inefficient.
class FriendSeen(models.Model):
    profile = models.ForeignKey(SteamProfile, related_name='friends_seen')
    to_friend = models.ForeignKey(SteamProfile, related_name='to_friend')
    current_name = models.CharField(max_length=128, default='', blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline', db_index=True)
    game = models.ForeignKey(Game, related_name='friends_seen', null=True, blank=True)
    created = models.DateTimeField(editable=False, default=timezone.now)

    def __unicode__(self):
        return u"{0} ({1})".format(self.to_friend.username, self.status)
