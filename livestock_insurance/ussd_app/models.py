from django.db import models
from datetime import datetime

class UserSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=20)
    stage = models.CharField(max_length=100)
    name = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    livestock_name = models.CharField(max_length=255, null=True, blank=True)
    package = models.CharField(max_length=50, null=True, blank=True)
    case_description = models.TextField(null=True, blank=True)
    payment_amount = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Session: {self.session_id}, Phone: {self.phone_number}, Stage: {self.stage}"

class LivestockRegistration(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    livestock_name = models.CharField(max_length=255)

    def __str__(self):
        return f"Location: {self.location}, Livestock Name: {self.livestock_name}"

class Claim(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    description = models.TextField()

    def __str__(self):
        return f"Claim for session: {self.session_id}"

class Payment(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    amount = models.IntegerField()

    def __str__(self):
        return f"Payment for session: {self.session_id}, Amount: {self.amount}"

class Service(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    # Add fields specific to the service

    def __str__(self):
        return f"Service for session: {self.session_id}"

class LivestockInsurance(models.Model):
    user_phone_number = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    livestock_name = models.CharField(max_length=255)
    package = models.CharField(max_length=50)
    case_description = models.TextField(blank=True, null=True)
    payment_amount = models.IntegerField(blank=True, null=True)
    registered_at = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f"{self.name}'s Livestock ({self.livestock_name})"


class CharityOrganization(models.Model):
    name = models.CharField(max_length=100)
    donation_type = models.CharField(max_length=100)

    def __str__(self):
        return self.name