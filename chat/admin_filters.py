from django.contrib import admin
from django.utils import timezone


class ActiveBanListFilter(admin.SimpleListFilter):
    """Admin filter for separation active and expired bans"""
    title = "active bans"
    parameter_name = "active"

    def lookups(self, request, model_admin):
        return [
            ("active", "active"),
            ("expired", "expired"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "active":
            return queryset.filter(time_end__gt=timezone.now())
        if self.value() == "expired":
            return queryset.filter(time_end__lt=timezone.now())
