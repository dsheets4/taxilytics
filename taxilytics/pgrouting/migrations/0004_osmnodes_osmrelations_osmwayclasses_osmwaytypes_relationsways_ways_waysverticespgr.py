# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-09-07 00:55
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pgrouting', '0003_routing_functions'),
    ]

    operations = [
        migrations.CreateModel(
            name='OsmNodes',
            fields=[
                ('node_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('osm_id', models.BigIntegerField(blank=True, null=True, unique=True)),
                ('lon', models.DecimalField(blank=True, decimal_places=8, max_digits=11, null=True)),
                ('lat', models.DecimalField(blank=True, decimal_places=8, max_digits=11, null=True)),
                ('numofuse', models.IntegerField(blank=True, null=True)),
                ('the_geom', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
            ],
            options={
                'db_table': 'osm_nodes',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='OsmRelations',
            fields=[
                ('relation_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('type_id', models.IntegerField(blank=True, null=True)),
                ('class_id', models.IntegerField(blank=True, null=True)),
                ('name', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'osm_relations',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='OsmWayClasses',
            fields=[
                ('class_id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True, null=True)),
                ('priority', models.FloatField(blank=True, null=True)),
                ('default_maxspeed', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'osm_way_classes',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='OsmWayTypes',
            fields=[
                ('type_id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'osm_way_types',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='RelationsWays',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('way_id', models.BigIntegerField(blank=True, null=True)),
                ('type', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'db_table': 'relations_ways',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Ways',
            fields=[
                ('gid', models.BigAutoField(primary_key=True, serialize=False)),
                ('length', models.FloatField(blank=True, null=True)),
                ('length_m', models.FloatField(blank=True, null=True)),
                ('name', models.TextField(blank=True, null=True)),
                ('x1', models.FloatField(blank=True, null=True)),
                ('y1', models.FloatField(blank=True, null=True)),
                ('x2', models.FloatField(blank=True, null=True)),
                ('y2', models.FloatField(blank=True, null=True)),
                ('cost', models.FloatField(blank=True, null=True)),
                ('reverse_cost', models.FloatField(blank=True, null=True)),
                ('cost_s', models.FloatField(blank=True, null=True)),
                ('reverse_cost_s', models.FloatField(blank=True, null=True)),
                ('rule', models.TextField(blank=True, null=True)),
                ('one_way', models.IntegerField(blank=True, null=True)),
                ('maxspeed_forward', models.IntegerField(blank=True, null=True)),
                ('maxspeed_backward', models.IntegerField(blank=True, null=True)),
                ('osm_id', models.BigIntegerField(blank=True, null=True)),
                ('source_osm', models.BigIntegerField(blank=True, null=True)),
                ('target_osm', models.BigIntegerField(blank=True, null=True)),
                ('priority', models.FloatField(blank=True, null=True)),
                ('the_geom', django.contrib.gis.db.models.fields.LineStringField(blank=True, null=True, srid=4326)),
            ],
            options={
                'db_table': 'ways',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='WaysVerticesPgr',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('osm_id', models.BigIntegerField(blank=True, null=True, unique=True)),
                ('cnt', models.IntegerField(blank=True, null=True)),
                ('chk', models.IntegerField(blank=True, null=True)),
                ('ein', models.IntegerField(blank=True, null=True)),
                ('eout', models.IntegerField(blank=True, null=True)),
                ('lon', models.DecimalField(blank=True, decimal_places=8, max_digits=11, null=True)),
                ('lat', models.DecimalField(blank=True, decimal_places=8, max_digits=11, null=True)),
                ('the_geom', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
            ],
            options={
                'db_table': 'ways_vertices_pgr',
                'managed': False,
            },
        ),
    ]