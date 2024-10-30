from django.db import models

class ArticleSummary(models.Model):
    link = models.URLField(unique=True)
    summary = models.TextField()

    def __str__(self):
        return self.link
    

    
