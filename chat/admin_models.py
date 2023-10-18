from django.contrib import admin
from django.utils import timezone

from chat.admin_filters import ActiveBanListFilter


class BanAdmin(admin.ModelAdmin):
    list_display = ('id', 'banned_user', 'chat_owner', 'banned_by', 'time_start',
                    'time_end', 'get_duration', 'get_remaining')
    list_display_links = ('id',)
    search_fields = ('banned_user__username', 'chat_owner__username', 'banned_by__username')
    list_filter = ('time_start', 'time_end', ActiveBanListFilter)
    fields = ('id', 'banned_user', 'chat_owner', 'banned_by', 'time_start', 'time_end', 'get_duration', 'get_remaining')
    readonly_fields = ('id', 'banned_user', 'chat_owner', 'banned_by', 'time_start', 'get_duration', 'get_remaining')

    def get_duration(self, object):
        return str(object.time_end - object.time_start)

    def get_remaining(self, object):
        now = timezone.now()
        if object.time_end > now:
            return str(object.time_end - now)
        else:
            return "Expired"

    get_duration.short_description = "Duration"
    get_remaining.short_description = "Remaining"
