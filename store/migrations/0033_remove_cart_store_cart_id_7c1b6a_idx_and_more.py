# Generated by Django 4.2.8 on 2024-11-27 04:30

import datetime
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0032_alter_order_expires_at_cart_store_cart_id_7c1b6a_idx_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='cart',
            name='store_cart_id_7c1b6a_idx',
        ),
        migrations.RemoveIndex(
            model_name='cartitem',
            name='store_carti_cart_id_1ecc31_idx',
        ),
        migrations.RemoveIndex(
            model_name='orderitem',
            name='store_order_order_i_ec571c_idx',
        ),
        migrations.RemoveIndex(
            model_name='product',
            name='store_produ_categor_49949e_idx',
        ),
        migrations.AlterField(
            model_name='cart',
            name='id',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='cart',
            name='session_key',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 27, 4, 45, 49, 979698, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['name', 'category', 'slug', 'unit_price', 'inventory'], name='store_produ_name_c1aa69_idx'),
        ),
    ]
