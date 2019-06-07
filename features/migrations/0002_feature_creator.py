# Generated by Django 2.1.1 on 2019-01-09 15:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('features', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='creator',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='features', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
