# Generated by Django 5.0.9 on 2024-12-03 01:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_rename_traffic_refresh_day_node_traffic_reset_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_rotation',
            field=models.IntegerField(null=True),
        ),
    ]