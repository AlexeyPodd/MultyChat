from django.contrib import admin

from .admin_models import BanAdmin
from .models import Ban


admin.site.register(Ban, BanAdmin)
