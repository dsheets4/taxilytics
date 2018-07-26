# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-21 01:08
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('streetcube', '0002_regionpartition'),
    ]

    operations = [
        migrations.AlterField(
            model_name='regionpartition',
            name='geometry',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(null=True, srid=3857),
        ),
    ]
