# Generated by Django 2.1.1 on 2019-01-09 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0007_remove_profile_nam'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='nam',
            field=models.CharField(default='', max_length=32),
        ),
    ]
