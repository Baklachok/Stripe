# Generated by Django 5.1.6 on 2025-03-02 01:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_discount_tax_order_discount_order_tax'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='currency',
            field=models.CharField(choices=[('usd', 'USD'), ('eur', 'EUR')], default='usd', max_length=3),
        ),
    ]
