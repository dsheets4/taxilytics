# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-09-25 01:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('streetcube', '0004_auto_20170907_0055'),
    ]

    operations = [
        migrations.AddField(
            model_name='regionpartition',
            name='system',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
