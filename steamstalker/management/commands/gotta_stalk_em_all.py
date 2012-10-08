from django.core.management.base import NoArgsCommand
from ...models import SteamProfile


class Command(NoArgsCommand):
    def handle_noargs(self, *args, **kwargs):
        for profile in SteamProfile.objects.filter(import_me=True):
            try:
                profile.get_latest_data()
            except Exception as e:
                # This sucks but lots of things can go wrong & it'd be better to
                # let as many complete as possible.
                print "{0} failed: {1}".format(profile.username, e)
