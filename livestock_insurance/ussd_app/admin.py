from django.contrib import admin
from .models import UserSession, Charity, Donation

class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'phone_number', 'stage', 'name', 'charity', 'donation_method', 'donation_amount', 'created_at', 'updated_at')

class CharityAdmin(admin.ModelAdmin):
    list_display = ('name',)

class DonationAdmin(admin.ModelAdmin):
    list_display = ('session', 'charity', 'donation_method', 'donation_amount', 'created_at', 'updated_at')

admin.site.register(UserSession, UserSessionAdmin)
admin.site.register(Charity, CharityAdmin)
admin.site.register(Donation, DonationAdmin)
