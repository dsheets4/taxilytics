"""
Created on Sep 8, 2015

@author: dingbat
"""
import json
from django.template import Library

register = Library()


def jsonify(value):
    return json.dumps(value)

register.filter('jsonify', jsonify)
