import uuid
from django.db import models

class Register(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    dob = models.DateField()
    password = models.CharField(max_length=128)
    height = models.IntegerField()
    gender = models.CharField(max_length=100)
