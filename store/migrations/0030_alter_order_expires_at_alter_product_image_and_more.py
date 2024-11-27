# Generated by Django 4.2.8 on 2024-11-27 04:03

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0029_alter_order_expires_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 27, 4, 18, 16, 643956, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, db_index=True, null=True, upload_to='sample/'),
        ),
        migrations.AlterField(
            model_name='product',
            name='inventory',
            field=models.PositiveIntegerField(db_index=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='unit_price',
            field=models.PositiveIntegerField(db_index=True),
        ),
    ]
