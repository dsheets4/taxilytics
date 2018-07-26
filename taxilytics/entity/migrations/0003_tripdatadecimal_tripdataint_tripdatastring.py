# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-01 13:31
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('entity', '0002_pd_functions'),
    ]

    operations = [
        migrations.CreateModel(
            name='TripDataDecimal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('columns', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=64), size=None)),
                ('ts', django.contrib.postgres.fields.ArrayField(base_field=models.DateTimeField(), size=None)),
                ('values', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=6, max_digits=20), size=None), size=None)),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_tripdatadecimal_set', to='entity.Trip')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TripDataInt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('columns', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=64), size=None)),
                ('ts', django.contrib.postgres.fields.ArrayField(base_field=models.DateTimeField(), size=None)),
                ('values', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), size=None), size=None)),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_tripdataint_set', to='entity.Trip')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TripDataString',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('columns', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=64), size=None)),
                ('ts', django.contrib.postgres.fields.ArrayField(base_field=models.DateTimeField(), size=None)),
                ('values', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256), size=None), size=None)),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_tripdatastring_set', to='entity.Trip')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]