# Generated by Django 2.1.1 on 2020-04-25 03:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pictureselfs', '0007_pictureself_edited_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='like',
            name='pictureself',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='pictureselfs.Pictureself'),
        ),
    ]
