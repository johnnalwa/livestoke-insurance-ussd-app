from django.contrib import admin
from .models import UserSession, UserDetail


admin.site.site_header = 'Kenya Census SystemL'
admin.site.site_title = 'KCS'
admin.site.index_title = ' Kenya Census System  ADMIN'
# Register your models here.

admin.site.register(UserSession)
admin.site.register(UserDetail)
