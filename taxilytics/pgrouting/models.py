# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.contrib.gis.db import models


class OsmNodes(models.Model):
    node_id = models.BigAutoField(primary_key=True)
    osm_id = models.BigIntegerField(unique=True, blank=True, null=True)
    lon = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    lat = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    numofuse = models.IntegerField(blank=True, null=True)
    the_geom = models.PointField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'osm_nodes'


class OsmRelations(models.Model):
    relation_id = models.BigIntegerField(primary_key=True)
    type_id = models.IntegerField(blank=True, null=True)
    class_id = models.IntegerField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'osm_relations'


class OsmWayClasses(models.Model):
    class_id = models.IntegerField(primary_key=True)
    type = models.ForeignKey('OsmWayTypes', models.DO_NOTHING, blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    priority = models.FloatField(blank=True, null=True)
    default_maxspeed = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'osm_way_classes'


class OsmWayTypes(models.Model):
    type_id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'osm_way_types'


class RelationsWays(models.Model):
    relation = models.ForeignKey(OsmRelations, models.DO_NOTHING, blank=True, null=True)
    way_id = models.BigIntegerField(blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'relations_ways'


class Ways(models.Model):
    """
    Edges in the road network graph.
    """
    gid = models.BigAutoField(primary_key=True)
    class_field = models.ForeignKey(OsmWayClasses, models.DO_NOTHING, db_column='class_id')  # Field renamed because it was a Python reserved word.
    length = models.FloatField(blank=True, null=True)
    length_m = models.FloatField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    source = models.ForeignKey('WaysVerticesPgr', models.DO_NOTHING, db_column='source', related_name='ways_source_set', blank=True, null=True)
    target = models.ForeignKey('WaysVerticesPgr', models.DO_NOTHING, db_column='target', related_name='ways_target_set', blank=True, null=True)
    x1 = models.FloatField(blank=True, null=True)
    y1 = models.FloatField(blank=True, null=True)
    x2 = models.FloatField(blank=True, null=True)
    y2 = models.FloatField(blank=True, null=True)
    cost = models.FloatField(blank=True, null=True)
    reverse_cost = models.FloatField(blank=True, null=True)
    cost_s = models.FloatField(blank=True, null=True)
    reverse_cost_s = models.FloatField(blank=True, null=True)
    rule = models.TextField(blank=True, null=True)
    one_way = models.IntegerField(blank=True, null=True)
    maxspeed_forward = models.IntegerField(blank=True, null=True)
    maxspeed_backward = models.IntegerField(blank=True, null=True)
    osm_id = models.BigIntegerField(blank=True, null=True)
    source_osm = models.BigIntegerField(blank=True, null=True)
    target_osm = models.BigIntegerField(blank=True, null=True)
    priority = models.FloatField(blank=True, null=True)
    the_geom = models.LineStringField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ways'


class WaysVerticesPgr(models.Model):
    """
    Vertices in the road network graph.
    """
    id = models.BigAutoField(primary_key=True)
    osm_id = models.BigIntegerField(unique=True, blank=True, null=True)
    cnt = models.IntegerField(blank=True, null=True)
    chk = models.IntegerField(blank=True, null=True)
    ein = models.IntegerField(blank=True, null=True)
    eout = models.IntegerField(blank=True, null=True)
    lon = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    lat = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    the_geom = models.PointField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ways_vertices_pgr'
