# Generated by Django 2.1.1 on 2020-05-01 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pictureselfs', '0009_auto_20200427_1123'),
    ]

    operations = [
        migrations.AddField(
            model_name='pictureself',
            name='tags',
            field=models.TextField(blank=True, max_length=500, null=True),
        ),
    ]