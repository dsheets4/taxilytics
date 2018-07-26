from django.contrib.gis.db import models


# Create your models here.

class Area(models.Model):
    name = models.CharField(max_length=64)
    geometry = models.MultiPolygonField(
        help_text='One or more polygons defining the area of interest.'
    )

    def __str__(self):
        return str(self.name)
