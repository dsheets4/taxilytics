from features.models import (
    Area,
)


# Create your tests here.

def create_area(name, geometry):
    return Area.objects.create(name=name, geometry=geometry)
