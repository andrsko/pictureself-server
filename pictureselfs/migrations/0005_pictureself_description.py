# Generated by Django 2.1.1 on 2019-02-02 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pictureselfs', '0004_remove_pictureself_original_feature_ids_json'),
    ]

    operations = [
        migrations.AddField(
            model_name='pictureself',
            name='description',
            field=models.TextField(blank=True, max_length=1000, null=True),
        ),
    ]
