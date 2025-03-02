from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Discount(models.Model):
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Фиксированная сумма скидки в валюте заказа")

    def __str__(self):
        return f"{self.name} (-${self.amount})"


class Tax(models.Model):
    name = models.CharField(max_length=255)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Процент налога (например, 10.00 для 10%)")

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class Order(models.Model):
    items = models.ManyToManyField(Item)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        """Вычисляет общую стоимость заказа с учетом скидки и налогов."""
        subtotal = sum(item.price for item in self.items.all())

        discount_amount = self.discount.amount if self.discount else 0
        taxed_amount = (subtotal - discount_amount) * (self.tax.percentage / 100) if self.tax else 0

        return max(subtotal - discount_amount + taxed_amount, 0)  # Итоговая сумма не может быть отрицательной

    def __str__(self):
        return f"Order {self.id} (Items: {self.items.count()})"
