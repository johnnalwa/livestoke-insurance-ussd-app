from django.db import models
from django.utils import timezone

created_at = timezone.now()
class UserSession(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20)
    stage = models.CharField(max_length=50)
    name = models.CharField(max_length=255, null=True, blank=True)
    charity = models.CharField(max_length=255, null=True, blank=True)
    donation_method = models.CharField(max_length=20, null=True, blank=True)
    donation_amount = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Charity(models.Model):
    name = models.CharField(max_length=255)

class Donation(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    charity = models.ForeignKey(Charity, on_delete=models.CASCADE)
    donation_method = models.CharField(max_length=20)
    donation_amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)