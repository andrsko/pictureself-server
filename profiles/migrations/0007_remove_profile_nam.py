# Generated by Django 2.1.1 on 2019-01-09 17:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_profile_nam'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='nam',
        ),
    ]
