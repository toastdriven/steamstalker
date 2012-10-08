from django.contrib import admin
from .models import Game, SteamProfile, FriendSeen


class GameAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['name', 'created']
    search_fields = ['name']


class SteamProfileAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['username', 'avatar_url', 'last_import', 'created']
    search_fields = ['username']


class FriendSeenAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['to_friend', 'profile', 'status', 'game', 'created']
    list_filter = ['game']


admin.site.register(Game, GameAdmin)
admin.site.register(SteamProfile, SteamProfileAdmin)
admin.site.register(FriendSeen, FriendSeenAdmin)
