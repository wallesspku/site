# Generated by Django 5.0.9 on 2024-11-27 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_relay_hidden_alter_node_idc_alter_node_ipv4_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mix',
            name='scope',
            field=models.CharField(default='edu', max_length=30),
        ),
    ]