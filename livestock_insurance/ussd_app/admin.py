from django.contrib import admin
from .models import UserSession, LivestockRegistration, Claim, Payment, Service, LivestockInsurance

class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'phone_number', 'stage', 'name', 'location', 'livestock_name', 'package', 'case_description', 'payment_amount')

class LivestockRegistrationAdmin(admin.ModelAdmin):
    list_display = ('session', 'location', 'livestock_name')

class ClaimAdmin(admin.ModelAdmin):
    list_display = ('session', 'description')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('session', 'amount')

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('session',)  # Add more fields specific to the service as needed

class LivestockInsuranceAdmin(admin.ModelAdmin):
    list_display = ('user_phone_number', 'name', 'location', 'livestock_name', 'package', 'case_description', 'payment_amount', 'registered_at')

admin.site.register(UserSession, UserSessionAdmin)
admin.site.register(LivestockRegistration, LivestockRegistrationAdmin)
admin.site.register(Claim, ClaimAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(LivestockInsurance, LivestockInsuranceAdmin)
