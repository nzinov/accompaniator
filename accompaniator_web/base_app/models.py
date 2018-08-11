from django.db import models


class Feedback(models.Model):
    session_key = models.CharField(max_length=32)
    rating = models.SmallIntegerField()
