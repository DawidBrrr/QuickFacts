from django.db import models

class ArticleSummary(models.Model):
    link = models.URLField(unique=True)
    title = models.CharField(max_length=255)
    summary = models.TextField()

    def __str__(self):
        return self.link
    

    
