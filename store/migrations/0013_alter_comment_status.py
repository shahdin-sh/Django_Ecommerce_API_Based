# Generated by Django 4.2.8 on 2024-08-24 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0012_customer_birth_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='status',
            field=models.CharField(choices=[('waiting', 'Waiting'), ('approved', 'Approved'), ('not approved', 'Not Approved')], default='waiting', max_length=100),
        ),
    ]