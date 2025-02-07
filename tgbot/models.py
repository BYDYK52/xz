from django.db import models

class Product(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    price = models.IntegerField()
    is_active = models.BooleanField(default=True)
    complexity = models.ForeignKey('Complexity', on_delete=models.PROTECT, null=True)
    who_made = models.ForeignKey('WhoMade', on_delete=models.PROTECT, null=True)

    def __str__(self):
        return self.title



class Complexity(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    def __str__(self):
        return self.title

class WhoMade(models.Model):
    title = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.title
