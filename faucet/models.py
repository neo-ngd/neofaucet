from django.db import models
from django.utils import timezone

# Create your models here.

class RequestNEO(models.Model):
    name = models.CharField(max_length=80)
    email = models.CharField(max_length=80)
    company = models.CharField(max_length=80)
    address = models.CharField(max_length=100)
    NEO = models.IntegerField()
    GAS = models.IntegerField()
    datetime = models.DateTimeField()

    def sendRequest(self):
        self.datetime = timezone.now()
        sself.save()

    def __str__(self):
        return self.name
