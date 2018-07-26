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
