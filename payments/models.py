from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Order(models.Model):
    items = models.ManyToManyField(Item)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        """Вычисляет общую стоимость заказа."""
        return sum(item.price for item in self.items.all())

    def __str__(self):
        return f"Order {self.id} (Items: {self.items.count()})"
