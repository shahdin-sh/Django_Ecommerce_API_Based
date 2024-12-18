# Generated by Django 4.2.8 on 2024-10-26 00:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0019_alter_cart_session_key'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cart',
            old_name='session_key',
            new_name='hashed_session_key',
        ),
        migrations.AddField(
            model_name='cart',
            name='is_session_key',
            field=models.BooleanField(default=False),
        ),
    ]
