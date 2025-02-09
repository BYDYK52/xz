from django.db import models
from rest_framework.authtoken.admin import User


class Product(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    price = models.IntegerField()
    is_active = models.BooleanField(default=True)
    complexity = models.ForeignKey('Complexity', on_delete=models.PROTECT, null=True)
    who_made = models.ForeignKey('WhoMade', on_delete=models.PROTECT, null=True)
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE,null=True)

    def str(self):
        return self.title

class Complexity(models.Model):
    title = models.CharField(max_length=100, db_index=True, null=True)
    def str(self):
        return self.title

class WhoMade(models.Model):
    title = models.CharField(max_length=100, db_index=True, null=True)

    def str(self):
        return self.title




class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE,null=True)
    quantity = models.IntegerField(default=0)
    created_timestamp = models.DateTimeField(auto_now_add=True)

    def str(self):
        return self.title