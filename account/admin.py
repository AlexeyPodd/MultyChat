from django.contrib import admin

from .admin_models import UserAdmin
from .models import User


admin.site.register(User, UserAdmin)

admin.site.site_title = "Multychat - Administration"
admin.site.site_header = "Multychat site administration"
