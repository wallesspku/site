# Generated by Django 5.0.13 on 2025-06-29 00:46

import django.db.models.deletion
import main.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_user_blocked_user_main_user_blocked_3e0780_idx'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbuseEvent',
            fields=[
                ('event_id', models.AutoField(primary_key=True, serialize=False)),
                ('ts', models.IntegerField(default=main.models.current_unix)),
                ('reason', models.CharField(max_length=50)),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='abuse_events', to='main.node')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='abuse_events', to='main.user')),
            ],
        ),
    ]
