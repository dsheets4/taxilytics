# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-09-25 01:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('entity', '0005_auto_20161129_1418'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tripdatadecimal',
            name='trip',
        ),
        migrations.RemoveField(
            model_name='tripdataint',
            name='trip',
        ),
        migrations.RemoveField(
            model_name='tripdatastring',
            name='trip',
        ),
        migrations.DeleteModel(
            name='TripDataDecimal',
        ),
        migrations.DeleteModel(
            name='TripDataInt',
        ),
        migrations.DeleteModel(
            name='TripDataString',
        ),
    ]
