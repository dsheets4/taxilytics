# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-08-28 06:29
from __future__ import unicode_literals

from django.db import migrations

from pgrouting import loader


class Migration(migrations.Migration):

    dependencies = [
        ('pgrouting', '0001_create_schema')
    ]

    operations = [
        migrations.RunPython(loader.forwards_func, loader.reverse_func),
    ]
