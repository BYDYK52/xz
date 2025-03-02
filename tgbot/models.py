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

    def __str__(self):
        return self.title

class Complexity(models.Model):
    title = models.CharField(max_length=100, db_index=True, null=True)
    def __str__(self):
        return self.title


class About(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()

    def __str__(self):
        return self.title

class WhoMade(models.Model):
    title = models.CharField(max_length=100, db_index=True, null=True)

    def __str__(self):
        return self.title



class BasketProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='basket')
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, related_name="basket_products")
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product} ({self.quantity})"
    def save(self, *args, **kwargs):
        if not self.id and( basket_product := BasketProduct.objects.filter(user=self.user, product=self.product).first()):
            basket_product.quantity += self.quantity
            self = basket_product

        return super().save(*args, **kwargs)


