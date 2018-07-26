"""
Created on Aug 18, 2014

@author: dingbat
"""

import json
import logging
import hashlib
import collections
import inspect
import os.path
import warnings
import re
from itertools import zip_longest
from copy import deepcopy

from math import radians, cos, sin, asin, sqrt, atan2, pi, degrees

from . import logger


class warn_deprecated(object):
    """
    Simple decorator to mark a function deprecated.  To actually see the
    messages you have to enable them in python either through the cmd line
        python -Wd
    or programmatically through
        import warnings
        warnings.simplefilter('default', deprecation_class)
    """

    def __init__(self, message, deprecation_class):
        self.message = message
        self.deprecation_class = deprecation_class

    def __call__(self, f):
        def wrapped(*args, **kwargs):
            warnings.warn(self.message, self.deprecation_class, 2)
            return f(*args, **kwargs)
        return wrapped


def grouper(iterable, n, fillvalue=None):
    """
    Returns the given iterable in groups of size n.  e.g.
    grouper([1,2,3,4,5], 2) iterates the following:
    [1,2]
    [3,4]
    [5,None]
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def make_enum(*sequential, **named):
    """
    Creates a python 3.4 enumeration from the passed in names which can simply
    be a list of names, which are assigned numbers starting at zero or they
    can be named using name=value.  Mixes are allowed but care should be taken
    to not repeat values where the repetition is not intended.  This function
    just makes creating enumerations more convenient.
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)


def hash_dict(d):
    """
    Creates a hash based on the sorted keys in a dictionary (for consistency)
    such that it's (sort-of) possible to differentiate the contained items by
    differences in the hash.
    """
    hashes = []
    for k, v in sorted(d.items()):
        if isinstance(v, collections.Mapping):
            hashes.append(hash_dict(d.get(k, {})))
        else:
            hashes.append(repr(d[k]))
    return ''.join(hashes)


def create_dir(dir_path):
    """
    If the indicated path does not exist, create it and return True
    If the indication path already exists as a directory, return False
    """
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
        return True
    else:
        return False


class OptionsCache(object):
    """
    Creates a directory that contains a json file with the "options" being
    stored.  Intended uses include serializing objects to unique folders
    based on the options used to create those objects.  For example, a topic
    model is calculated based on input parameters and the model is serialized
    to disk.  The options cache can generate a folder allowing a future request
    for a model with the same options to be located retrieved from disk instead
    of recalculating.
    """

    def __init__(self, options, cache_dir):
        self.opts = options
        self.cache_dir = os.path.normpath(
            '{}/{}'.format(cache_dir, self._hash())
        )

        self.new = create_dir(self.cache_dir)

        self.save()

    def _hash(self):
        return hashlib.sha1(
            hash_dict(self.opts).encode('utf-8')
        ).hexdigest()

    def save(self):
        filename = '{}/options.json'.format(self.cache_dir)
        with open(filename, 'w') as f:
            json.dump(self.opts, f, indent=4)
            logger.info(
                "Options saved to {}".format(filename)
            )

    def load(self):
        filename = '{}/options.json'.format(self.cache_dir)
        with open(filename, 'r') as f:
            self.opts = json.load(f)
        logger.info(
            "Options loaded from {}".format(filename)
        )


def setup_logging(args, the_logger):
    """
    Default values related to setting up python logging.  Provides the ability
    to globally manage the log outputs from miscellaneous modules through a
    common configuration.
    """
    the_logger = the_logger or logging.getLogger(__name__)
    log_format = '%(asctime)s : %(levelname)s " %(message)s'
    log_config = {'format': log_format, 'level': logging.INFO}
    if args:
        if args.debug:
            log_config['level'] = logging.DEBUG
        if args.log_file and len(args.log_file) > 0:
            log_config['filename'] = args.log_file
    the_logger.basicConfig(**log_config)

    return the_logger


def default_args(parser):
    """
    Each executable porition of the application provides a default set of
    arguments that must be setup each time.  This simply abstracts the
    interface for the values and reduces code setup.
    """
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Enable extra output.")
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        dest="debug",
        default=False,
        help="Enable output useful for debugging.")
    parser.add_argument(
        "-L", "--log-file",
        dest="log_file",
        default=None,
        help="Location to write log file, stderr is default.")


def filter_kwargs(call_obj, kwargs):
    """
    Takes in a callable and a dictionary.  Returns a three tuple
    (applicable_kwargs, removed_kwargs, not_set_kwargs) where

    * applicable_kwargs is a dictionary containing only keys from the passed in
      kwargs that the callable expects.
    * removed_kwargs is a list of the items that were in the passed in kwargs
      but not expected by the callable object.
    * not_set_kwargs is a list of the arguments expected by the callable object
      that were in the passed in kwargs.
    """
    arg_spec = inspect.getargspec(call_obj)
    if arg_spec.keywords is not None:
        return kwargs.copy(), [], []
    else:
        unset_args = []
        unused_args = []
        new_kwargs = {}
        for a in arg_spec.args:
            if a in kwargs:
                new_kwargs[a] = kwargs[a]
            else:
                unset_args.append(a)
        for v in kwargs:
            if v not in new_kwargs:
                unused_args.append(v)
        return new_kwargs, unused_args, unset_args


def load_item(item):
    """ Adapted from unittest loadTestsFromName
    This takes in a dotted notation string and attempts to load the item
    referenced by the string.  The final referenced item is returned.  This is
    useful for implementing features such as the callable wrapper who's
    configuration takes in the string reference to a callable and abstracts
    management of the arguments.  For example, the string:
    'util.general.load_item' would return this function.
    """
    parts = item.split('.')

    # Attempt to load the module and progressively slice off the portion
    # at the end.  The longest import-able sequence is the module and the
    # rest should represent a django model manager within.
    parts_copy = parts[:]
    while parts_copy:
        try:
            module = __import__('.'.join(parts_copy))
            break
        except ImportError:
            del parts_copy[-1]
            if not parts_copy:
                raise
    parts = parts[1:]
    obj = module

    # Now that the module is loaded, get the requested item
    for part in parts:
        obj = getattr(obj, part)

    return obj


def option_list(call_obj):
    """ Returns the argument list for the provided callable object """
    return [a for a in inspect.getargspec(call_obj)]


# The following was inspired by
# :http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
def update_dict(d, u, copy=False):
    """
    Update the dictionary 'd' using values in dictionary 'u', similar to
    dict.update except that this will recursively traverse any nested
    dictionaries.
    """
    if copy:
        d = deepcopy(d)
    for k, v in u.items():
        if isinstance(v, dict):
            r = update_dict(d.get(k, {}), v)
            d[k] = r
        elif k in d and isinstance(d[k], list):
            d[k].extend(v if isinstance(v, list) else [v])
        else:
            d[k] = v
    return d


def dict_combiner(*args):
    """
    Convenience function that creates a new dictionary by combining the passed
    in dictionaries.  Useful for creating a few partial argument dictionary
    and then combining them to create a single named argument list using **.
    """
    combined = {}
    for d in args:
        update_dict(combined, d)
    return combined


def haversine(lon_lat_1, lon_lat_2):
    """
    Approximate great circle distance in kilometers between two WGS84 points.
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [
        lon_lat_1[0], lon_lat_1[1],
        lon_lat_2[0], lon_lat_2[1]
    ])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))

    # The currently accepted (WGS84) radius at the equator is 6378.137 km and
    # 6356.752 km at the polar caps. For aviation purposes the FAI uses a
    # radius of 6371.0 km
    km = 6367.4445 * c
    return km


def coord_distance_threshold(coords, threshold):
    """
    Returns True is the spherical distance between each point is less than the
    provided distance threshold (km).
    """

    try:
        prev_coord = None
        for i, coord in enumerate(coords):
            if i > 0 and haversine(prev_coord, coord) > threshold:
                return False
            prev_coord = coord
    except:
        raise
        return False

    return True


def angle_trunc(a):
    while a < 0.0:
        a += pi * 2
    return a


def initial_bearing(pointA, pointB):
    """
    Calculates the bearing between two points.
    The formula used is the following:
        ? = atan2(sin(?long).cos(lat2),
                  cos(lat1).sin(lat2) ? sin(lat1).cos(lat2).cos(?long))

    Adapted from: https://gist.github.com/jeromer/2005586

    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = radians(pointA[1])
    lat2 = radians(pointB[1])

    diffLong = radians(pointB[0] - pointA[0])

    x = sin(diffLong) * cos(lat2)
    y = cos(lat1) * sin(lat2) - (sin(lat1)
            * cos(lat2) * cos(diffLong))

    return atan2(x, y)


def initial_bearing_compass(pointA, pointB):
    # Now we have the initial bearing but math.atan2 return values
    # from -180 to + 180 which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial = degrees(initial_bearing(pointA, pointB))
    compass = (initial + 360) % 360

    return compass


def try_int(s):
    try:
        return int(s)
    except ValueError:
        return s


NUM_RE = re.compile(r'([0-9]+)')


def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [int(c) if c.isdigit() else c for c in NUM_RE.split(s)]


def sort_nicely(l):
    """ Sort the given list in the way that humans expect. """
    l.sort(key=alphanum_key)
    return l


def heading_delta(hdg1, hdg2):
    """
    Calculates the difference in heading with positive right and negative left.
    Note that this is assuming bidirectional headings so headings greater than
    180 are reversed.  e.g. a heading of 210 is turned to 30.
    """
    delta = hdg2 - hdg1
    if delta > 180:
        delta = delta - 360
    elif delta < -180:
        delta = delta + 360
    if delta > 90:
        delta = delta - 180
    elif delta < -90:
        delta = delta + 180
    return delta
