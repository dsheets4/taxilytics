from django.contrib.gis.db import models

from django.contrib.postgres.fields import HStoreField, ArrayField


def hstore_string_to_dict(s):
    if not s:
        return {}
    return dict((
        (h.replace('"', '').replace(' ', '') for h in i.split('=>'))
        for i in s.split(',')
    ))


class PlanetOsmLineManager(models.Manager):
    """
    Manager for Entity objects.  It primarily defines the natural keys but
    is useful for other features such as default query functions.
    """

    def roads(self):
        return self.filter(highway__isnull=False)


class PlanetOsmLine(models.Model):
    osm_id = models.BigIntegerField(blank=True, null=True)
    access = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_housename = models.TextField(
        db_column='addr:housename', blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_housenumber = models.TextField(
        db_column='addr:housenumber', blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_interpolation = models.TextField(
        db_column='addr:interpolation', blank=True, null=True)
    admin_level = models.TextField(blank=True, null=True)
    aerialway = models.TextField(blank=True, null=True)
    aeroway = models.TextField(blank=True, null=True)
    amenity = models.TextField(blank=True, null=True)
    area = models.TextField(blank=True, null=True)
    barrier = models.TextField(blank=True, null=True)
    bicycle = models.TextField(blank=True, null=True)
    brand = models.TextField(blank=True, null=True)
    bridge = models.TextField(blank=True, null=True)
    boundary = models.TextField(blank=True, null=True)
    building = models.TextField(blank=True, null=True)
    construction = models.TextField(blank=True, null=True)
    covered = models.TextField(blank=True, null=True)
    culvert = models.TextField(blank=True, null=True)
    cutting = models.TextField(blank=True, null=True)
    denomination = models.TextField(blank=True, null=True)
    disused = models.TextField(blank=True, null=True)
    embankment = models.TextField(blank=True, null=True)
    foot = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    generator_source = models.TextField(
        db_column='generator:source', blank=True, null=True)
    harbour = models.TextField(blank=True, null=True)
    highway = models.TextField(blank=True, null=True)
    historic = models.TextField(blank=True, null=True)
    horse = models.TextField(blank=True, null=True)
    intermittent = models.TextField(blank=True, null=True)
    junction = models.TextField(blank=True, null=True)
    landuse = models.TextField(blank=True, null=True)
    layer = models.TextField(blank=True, null=True)
    leisure = models.TextField(blank=True, null=True)
    lock = models.TextField(blank=True, null=True)
    man_made = models.TextField(blank=True, null=True)
    military = models.TextField(blank=True, null=True)
    motorcar = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    natural = models.TextField(blank=True, null=True)
    office = models.TextField(blank=True, null=True)
    oneway = models.TextField(blank=True, null=True)
    operator = models.TextField(blank=True, null=True)
    place = models.TextField(blank=True, null=True)
    population = models.TextField(blank=True, null=True)
    power = models.TextField(blank=True, null=True)
    power_source = models.TextField(blank=True, null=True)
    public_transport = models.TextField(blank=True, null=True)
    railway = models.TextField(blank=True, null=True)
    ref = models.TextField(blank=True, null=True)
    religion = models.TextField(blank=True, null=True)
    route = models.TextField(blank=True, null=True)
    service = models.TextField(blank=True, null=True)
    shop = models.TextField(blank=True, null=True)
    sport = models.TextField(blank=True, null=True)
    surface = models.TextField(blank=True, null=True)
    toll = models.TextField(blank=True, null=True)
    tourism = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    tower_type = models.TextField(
        db_column='tower:type', blank=True, null=True)
    tracktype = models.TextField(blank=True, null=True)
    tunnel = models.TextField(blank=True, null=True)
    water = models.TextField(blank=True, null=True)
    waterway = models.TextField(blank=True, null=True)
    wetland = models.TextField(blank=True, null=True)
    width = models.TextField(blank=True, null=True)
    wood = models.TextField(blank=True, null=True)
    z_order = models.IntegerField(blank=True, null=True)
    way_area = models.FloatField(blank=True, null=True)
    tags = HStoreField(blank=True, null=True)
    way = models.LineStringField(srid=3857, blank=True, null=True)
    gid = models.AutoField(primary_key=True)
    # objects = models.GeoManager()
    objects = PlanetOsmLineManager()

    class Meta:
        managed = False
        db_table = 'planet_osm_line'

    def __str__(self):
        tags = hstore_string_to_dict(self.tags)
        return tags.get('name:en', tags.get('name:pinyin', self.name)) or 'undefined'


class PlanetOsmNodes(models.Model):
    id = models.BigIntegerField(primary_key=True)
    lat = models.IntegerField()
    lon = models.IntegerField()
    # May not be right...
    tags = ArrayField(models.TextField(blank=True, null=True))

    class Meta:
        managed = False
        db_table = 'planet_osm_nodes'


class PlanetOsmPoint(models.Model):
    osm_id = models.BigIntegerField(blank=True, null=True)
    access = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_housename = models.TextField(
        db_column='addr:housename', blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_housenumber = models.TextField(
        db_column='addr:housenumber', blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_interpolation = models.TextField(
        db_column='addr:interpolation', blank=True, null=True)
    admin_level = models.TextField(blank=True, null=True)
    aerialway = models.TextField(blank=True, null=True)
    aeroway = models.TextField(blank=True, null=True)
    amenity = models.TextField(blank=True, null=True)
    area = models.TextField(blank=True, null=True)
    barrier = models.TextField(blank=True, null=True)
    bicycle = models.TextField(blank=True, null=True)
    brand = models.TextField(blank=True, null=True)
    bridge = models.TextField(blank=True, null=True)
    boundary = models.TextField(blank=True, null=True)
    building = models.TextField(blank=True, null=True)
    capital = models.TextField(blank=True, null=True)
    construction = models.TextField(blank=True, null=True)
    covered = models.TextField(blank=True, null=True)
    culvert = models.TextField(blank=True, null=True)
    cutting = models.TextField(blank=True, null=True)
    denomination = models.TextField(blank=True, null=True)
    disused = models.TextField(blank=True, null=True)
    ele = models.TextField(blank=True, null=True)
    embankment = models.TextField(blank=True, null=True)
    foot = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    generator_source = models.TextField(
        db_column='generator:source', blank=True, null=True)
    harbour = models.TextField(blank=True, null=True)
    highway = models.TextField(blank=True, null=True)
    historic = models.TextField(blank=True, null=True)
    horse = models.TextField(blank=True, null=True)
    intermittent = models.TextField(blank=True, null=True)
    junction = models.TextField(blank=True, null=True)
    landuse = models.TextField(blank=True, null=True)
    layer = models.TextField(blank=True, null=True)
    leisure = models.TextField(blank=True, null=True)
    lock = models.TextField(blank=True, null=True)
    man_made = models.TextField(blank=True, null=True)
    military = models.TextField(blank=True, null=True)
    motorcar = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    natural = models.TextField(blank=True, null=True)
    office = models.TextField(blank=True, null=True)
    oneway = models.TextField(blank=True, null=True)
    operator = models.TextField(blank=True, null=True)
    place = models.TextField(blank=True, null=True)
    poi = models.TextField(blank=True, null=True)
    population = models.TextField(blank=True, null=True)
    power = models.TextField(blank=True, null=True)
    power_source = models.TextField(blank=True, null=True)
    public_transport = models.TextField(blank=True, null=True)
    railway = models.TextField(blank=True, null=True)
    ref = models.TextField(blank=True, null=True)
    religion = models.TextField(blank=True, null=True)
    route = models.TextField(blank=True, null=True)
    service = models.TextField(blank=True, null=True)
    shop = models.TextField(blank=True, null=True)
    sport = models.TextField(blank=True, null=True)
    surface = models.TextField(blank=True, null=True)
    toll = models.TextField(blank=True, null=True)
    tourism = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    tower_type = models.TextField(
        db_column='tower:type', blank=True, null=True)
    tunnel = models.TextField(blank=True, null=True)
    water = models.TextField(blank=True, null=True)
    waterway = models.TextField(blank=True, null=True)
    wetland = models.TextField(blank=True, null=True)
    width = models.TextField(blank=True, null=True)
    wood = models.TextField(blank=True, null=True)
    z_order = models.IntegerField(blank=True, null=True)
    tags = HStoreField(blank=True, null=True)
    way = models.PointField(srid=3857, blank=True, null=True)
    gid = models.AutoField(primary_key=True)
    objects = models.GeoManager()

    class Meta:
        managed = False
        db_table = 'planet_osm_point'


class PlanetOsmPolygon(models.Model):
    osm_id = models.BigIntegerField(blank=True, null=True)
    access = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_housename = models.TextField(
        db_column='addr:housename', blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_housenumber = models.TextField(
        db_column='addr:housenumber', blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_interpolation = models.TextField(
        db_column='addr:interpolation', blank=True, null=True)
    admin_level = models.TextField(blank=True, null=True)
    aerialway = models.TextField(blank=True, null=True)
    aeroway = models.TextField(blank=True, null=True)
    amenity = models.TextField(blank=True, null=True)
    area = models.TextField(blank=True, null=True)
    barrier = models.TextField(blank=True, null=True)
    bicycle = models.TextField(blank=True, null=True)
    brand = models.TextField(blank=True, null=True)
    bridge = models.TextField(blank=True, null=True)
    boundary = models.TextField(blank=True, null=True)
    building = models.TextField(blank=True, null=True)
    construction = models.TextField(blank=True, null=True)
    covered = models.TextField(blank=True, null=True)
    culvert = models.TextField(blank=True, null=True)
    cutting = models.TextField(blank=True, null=True)
    denomination = models.TextField(blank=True, null=True)
    disused = models.TextField(blank=True, null=True)
    embankment = models.TextField(blank=True, null=True)
    foot = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    generator_source = models.TextField(
        db_column='generator:source', blank=True, null=True)
    harbour = models.TextField(blank=True, null=True)
    highway = models.TextField(blank=True, null=True)
    historic = models.TextField(blank=True, null=True)
    horse = models.TextField(blank=True, null=True)
    intermittent = models.TextField(blank=True, null=True)
    junction = models.TextField(blank=True, null=True)
    landuse = models.TextField(blank=True, null=True)
    layer = models.TextField(blank=True, null=True)
    leisure = models.TextField(blank=True, null=True)
    lock = models.TextField(blank=True, null=True)
    man_made = models.TextField(blank=True, null=True)
    military = models.TextField(blank=True, null=True)
    motorcar = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    natural = models.TextField(blank=True, null=True)
    office = models.TextField(blank=True, null=True)
    oneway = models.TextField(blank=True, null=True)
    operator = models.TextField(blank=True, null=True)
    place = models.TextField(blank=True, null=True)
    population = models.TextField(blank=True, null=True)
    power = models.TextField(blank=True, null=True)
    power_source = models.TextField(blank=True, null=True)
    public_transport = models.TextField(blank=True, null=True)
    railway = models.TextField(blank=True, null=True)
    ref = models.TextField(blank=True, null=True)
    religion = models.TextField(blank=True, null=True)
    route = models.TextField(blank=True, null=True)
    service = models.TextField(blank=True, null=True)
    shop = models.TextField(blank=True, null=True)
    sport = models.TextField(blank=True, null=True)
    surface = models.TextField(blank=True, null=True)
    toll = models.TextField(blank=True, null=True)
    tourism = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    tower_type = models.TextField(
        db_column='tower:type', blank=True, null=True)
    tracktype = models.TextField(blank=True, null=True)
    tunnel = models.TextField(blank=True, null=True)
    water = models.TextField(blank=True, null=True)
    waterway = models.TextField(blank=True, null=True)
    wetland = models.TextField(blank=True, null=True)
    width = models.TextField(blank=True, null=True)
    wood = models.TextField(blank=True, null=True)
    z_order = models.IntegerField(blank=True, null=True)
    way_area = models.FloatField(blank=True, null=True)
    tags = HStoreField(blank=True, null=True)
    way = models.GeometryField(srid=3857, blank=True, null=True)
    gid = models.AutoField(primary_key=True)
    objects = models.GeoManager()

    class Meta:
        managed = False
        db_table = 'planet_osm_polygon'


class PlanetOsmRels(models.Model):
    id = models.BigIntegerField(primary_key=True)
    way_off = models.SmallIntegerField(blank=True, null=True)
    rel_off = models.SmallIntegerField(blank=True, null=True)
    # May not be right...
    parts = ArrayField(models.BigIntegerField(blank=True, null=True))
    # May not be right...
    members = ArrayField(models.TextField(blank=True, null=True))
    # May not be right...
    tags = ArrayField(models.TextField(blank=True, null=True))

    class Meta:
        managed = False
        db_table = 'planet_osm_rels'


class PlanetOsmRoads(models.Model):
    osm_id = models.BigIntegerField(blank=True, null=True)
    access = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_housename = models.TextField(
        db_column='addr:housename', blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_housenumber = models.TextField(
        db_column='addr:housenumber', blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    addr_interpolation = models.TextField(
        db_column='addr:interpolation', blank=True, null=True)
    admin_level = models.TextField(blank=True, null=True)
    aerialway = models.TextField(blank=True, null=True)
    aeroway = models.TextField(blank=True, null=True)
    amenity = models.TextField(blank=True, null=True)
    area = models.TextField(blank=True, null=True)
    barrier = models.TextField(blank=True, null=True)
    bicycle = models.TextField(blank=True, null=True)
    brand = models.TextField(blank=True, null=True)
    bridge = models.TextField(blank=True, null=True)
    boundary = models.TextField(blank=True, null=True)
    building = models.TextField(blank=True, null=True)
    construction = models.TextField(blank=True, null=True)
    covered = models.TextField(blank=True, null=True)
    culvert = models.TextField(blank=True, null=True)
    cutting = models.TextField(blank=True, null=True)
    denomination = models.TextField(blank=True, null=True)
    disused = models.TextField(blank=True, null=True)
    embankment = models.TextField(blank=True, null=True)
    foot = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    generator_source = models.TextField(
        db_column='generator:source', blank=True, null=True)
    harbour = models.TextField(blank=True, null=True)
    highway = models.TextField(blank=True, null=True)
    historic = models.TextField(blank=True, null=True)
    horse = models.TextField(blank=True, null=True)
    intermittent = models.TextField(blank=True, null=True)
    junction = models.TextField(blank=True, null=True)
    landuse = models.TextField(blank=True, null=True)
    layer = models.TextField(blank=True, null=True)
    leisure = models.TextField(blank=True, null=True)
    lock = models.TextField(blank=True, null=True)
    man_made = models.TextField(blank=True, null=True)
    military = models.TextField(blank=True, null=True)
    motorcar = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    natural = models.TextField(blank=True, null=True)
    office = models.TextField(blank=True, null=True)
    oneway = models.TextField(blank=True, null=True)
    operator = models.TextField(blank=True, null=True)
    place = models.TextField(blank=True, null=True)
    population = models.TextField(blank=True, null=True)
    power = models.TextField(blank=True, null=True)
    power_source = models.TextField(blank=True, null=True)
    public_transport = models.TextField(blank=True, null=True)
    railway = models.TextField(blank=True, null=True)
    ref = models.TextField(blank=True, null=True)
    religion = models.TextField(blank=True, null=True)
    route = models.TextField(blank=True, null=True)
    service = models.TextField(blank=True, null=True)
    shop = models.TextField(blank=True, null=True)
    sport = models.TextField(blank=True, null=True)
    surface = models.TextField(blank=True, null=True)
    toll = models.TextField(blank=True, null=True)
    tourism = models.TextField(blank=True, null=True)
    # Field renamed to remove unsuitable characters.
    tower_type = models.TextField(
        db_column='tower:type', blank=True, null=True)
    tracktype = models.TextField(blank=True, null=True)
    tunnel = models.TextField(blank=True, null=True)
    water = models.TextField(blank=True, null=True)
    waterway = models.TextField(blank=True, null=True)
    wetland = models.TextField(blank=True, null=True)
    width = models.TextField(blank=True, null=True)
    wood = models.TextField(blank=True, null=True)
    z_order = models.IntegerField(blank=True, null=True)
    way_area = models.FloatField(blank=True, null=True)
    tags = HStoreField(blank=True, null=True)
    way = models.LineStringField(srid=3857, blank=True, null=True)
    gid = models.AutoField(primary_key=True)
    objects = models.GeoManager()

    class Meta:
        managed = False
        db_table = 'planet_osm_roads'


class PlanetOsmWays(models.Model):
    id = models.BigIntegerField(primary_key=True)
    nodes = ArrayField(models.BigIntegerField())  # May not be right...
    # May not be right...
    tags = ArrayField(models.TextField(blank=True, null=True))

    class Meta:
        managed = False
        db_table = 'planet_osm_ways'
