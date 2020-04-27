# Generated by Django 2.1.1 on 2020-04-27 08:23

from django.db import migrations, models
import pictureselfs.models


class Migration(migrations.Migration):

    dependencies = [
        ('pictureselfs', '0008_auto_20200425_0620'),
    ]

    operations = [
        migrations.AddField(
            model_name='pictureself',
            name='image',
            field=models.ImageField(null=True, upload_to=pictureselfs.models.get_file_path),
        ),
        migrations.AddField(
            model_name='pictureself',
            name='image_original_name',
            field=models.CharField(max_length=200, null=True),
        ),
    ]