from django.db import models

class UserSession(models.Model):
    session_id = models.CharField(max_length=100, primary_key=True)
    phone_number = models.CharField(max_length=20)
    stage = models.CharField(max_length=20)
    name = models.CharField(max_length=100, blank=True, null=True)
    id_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"Session: {self.session_id}, Phone: {self.phone_number}"

class UserDetail(models.Model):
    phone_number = models.CharField(max_length=20)
    full_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20, primary_key=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=1)
    registration_date = models.DateField()
    registration_time = models.TimeField()

    def __str__(self):
        return f"User: {self.full_name}, Phone: {self.phone_number}"
