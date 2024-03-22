from django.contrib import admin
from .models import UserSession, UserDetail

# Register your models here.

admin.site.register(UserSession)
admin.site.register(UserDetail)
