# Generated by Django 2.1.1 on 2019-01-31 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pictureselfs', '0004_remove_pictureself_original_feature_ids_json'),
        ('variants', '0004_auto_20190127_2117'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='variant',
            name='pictureself',
        ),
        migrations.AddField(
            model_name='variant',
            name='pictureselfs',
            field=models.ManyToManyField(related_name='variants', to='pictureselfs.Pictureself'),
        ),
    ]
