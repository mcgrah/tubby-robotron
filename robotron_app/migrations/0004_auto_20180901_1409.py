# Generated by Django 2.1 on 2018-09-01 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('robotron_app', '0003_auto_20180824_1746'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='delivery_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='character',
            name='delivery_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
