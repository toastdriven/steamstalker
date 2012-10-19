from django.contrib import admin
from .models import Game, SteamProfile, SteamFriend, ProfileSeen


class GameAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['name', 'created']
    search_fields = ['name']


class SteamProfileAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['username', 'last_import', 'import_me', 'created']
    list_filter = ['import_me']
    search_fields = ['username']


class SteamFriendAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['from_friend', 'to_friend', 'created']


class ProfileSeenAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['seen', 'current_name', 'status', 'game', 'created']
    list_filter = ['game']


admin.site.register(Game, GameAdmin)
admin.site.register(SteamProfile, SteamProfileAdmin)
admin.site.register(SteamFriend, SteamFriendAdmin)
admin.site.register(ProfileSeen, ProfileSeenAdmin)
