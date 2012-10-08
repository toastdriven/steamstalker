from django.core.management.base import NoArgsCommand
from ...models import SteamProfile


class Command(NoArgsCommand):
    def handle_noargs(self, *args, **kwargs):
        for profile in SteamProfile.objects.filter(import_me=True):
            profile.get_latest_data()
