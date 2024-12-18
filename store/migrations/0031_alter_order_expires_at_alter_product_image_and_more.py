# Generated by Django 4.2.8 on 2024-11-27 04:07

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0030_alter_order_expires_at_alter_product_image_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 27, 4, 22, 26, 275626, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='sample/'),
        ),
        migrations.AlterField(
            model_name='product',
            name='inventory',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='unit_price',
            field=models.PositiveIntegerField(),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category', 'slug', 'unit_price', 'inventory', 'image'], name='store_produ_categor_49949e_idx'),
        ),
    ]
