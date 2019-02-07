from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Notes(models.Model):
    title = models.CharField(max_length=100)
    note_text = models.TextField()
    last_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Note_Tag(models.Model):
    note = models.ForeignKey(Notes, on_delete=models.CASCADE)
    tag_text = models.CharField(max_length=50)
