from django.db import models


class Feedback(models.Model):
    song_name = models.CharField(max_length=32)
    session_key = models.CharField(max_length=32)
    rating = models.SmallIntegerField()
