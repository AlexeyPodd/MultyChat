from django.contrib import admin


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'username_slug', 'email', 'allowed_run_chat',
                    'is_running_chat', 'is_staff', 'is_active')
    list_display_links = ('id', 'username', 'username_slug', 'email')
    search_fields = ('username', 'username_slug', 'email')
    list_filter = ('allowed_run_chat', 'is_staff', 'is_active')
    fields = ('username', 'username_slug', 'email', 'allowed_run_chat',
              'is_running_chat', 'is_staff', 'is_active')
    readonly_fields = ('username', 'username_slug', 'email', 'is_running_chat')
