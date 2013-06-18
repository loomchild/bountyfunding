from django.db import models

class Issue(models.Model):
	summary = models.CharField(max_length=200)
	description = models.CharField(max_length=2000)
	amount = models.IntegerField()

