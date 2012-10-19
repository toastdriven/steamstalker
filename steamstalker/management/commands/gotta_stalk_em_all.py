from django.core.management.base import NoArgsCommand
from django.utils import timezone
from ...models import SteamProfile


class Command(NoArgsCommand):
    def handle_noargs(self, *args, **kwargs):
        import_time = timezone.now()

        for profile in SteamProfile.objects.filter(import_me=True):
            if profile.username != 'favicon.ico':
                try:
                    profile.get_latest_data(imported_at=import_time)
                except Exception as e:
                    # This sucks but lots of things can go wrong & it'd be better to
                    # let as many complete as possible.
                    print "{0} failed: {1}".format(profile.username, e)
