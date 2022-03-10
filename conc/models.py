from django.db import models
from django.contrib.auth.models import User

class TempScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)
