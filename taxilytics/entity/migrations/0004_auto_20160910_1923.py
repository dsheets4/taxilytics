# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-10 19:23
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entity', '0003_tripdatadecimal_tripdataint_tripdatastring'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tripdatadecimal',
            name='columns',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=64), db_index=True, size=None),
        ),
        migrations.AlterField(
            model_name='tripdataint',
            name='columns',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=64), db_index=True, size=None),
        ),
        migrations.AlterField(
            model_name='tripdatastring',
            name='columns',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=64), db_index=True, size=None),
        ),
    ]