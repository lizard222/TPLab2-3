from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal 

class Faction(models.Model):
    name = models.CharField(max_length=100)  # Space Marines, Chaos, etc.
    description = models.TextField()
    logo = models.ImageField(upload_to='factions/')

class Product(models.Model):
    PRODUCT_TYPES = [
        ('MINIATURE', 'Миниатюры'),
        ('STARTER_SET', 'Стартовый набор'),
        ('PAINT', 'Краски'),
        ('ACCESSORY', 'Аксессуары'),
        ('BOOK', 'Книги правил'),
    ]
    
    name = models.CharField(max_length=200)
    faction = models.ForeignKey(Faction, on_delete=models.CASCADE, null=True, blank=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    is_preorder = models.BooleanField(default=False)
    release_date = models.DateField(null=True, blank=True)  # для предзаказов
    image = models.ImageField(upload_to='products/')
    
    def get_discounted_price(self):
        # Скидка 10% на стартовые наборы
        if self.product_type == 'STARTER_SET':
            return self.price * Decimal('0.9')
        return self.price

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def total_price(self):
        return self.product.get_discounted_price() * self.quantity

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(CartItem)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='PENDING')