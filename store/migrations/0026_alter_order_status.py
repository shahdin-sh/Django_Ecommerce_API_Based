# Generated by Django 4.2.8 on 2024-11-18 02:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0025_alter_wishlist_products'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('paid', 'Paid'), ('unpaid', 'Unpaid')], default='unpaid', max_length=255),
        ),
    ]
