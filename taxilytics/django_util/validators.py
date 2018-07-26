import json

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _


@deconstructible
class JsonValidator(object):

    def __init__(self, required_fields=None):
        self.required_fields = set(required_fields or [])

    def __call__(self, value):
        # If it's not a dict then the value is bad but try to convert to JSON
        # to generate a more helpful error message.
        if not isinstance(value, dict):
            try:
                value = json.loads(value)
            except ValueError as e:
                print('Invalid JSON: %s' % str(e))
                raise ValidationError(_(
                    'Invalid JSON: %s' % str(e)
                ))

        # Check for required fields.
        missing_fields = []
        for req in self.required_fields:
            if req not in value:
                missing_fields.append(req)
        if len(missing_fields) > 0:
            raise ValidationError(_(
                'Missing required fields: %s' % ','.join(missing_fields)
            ))

    def __eq__(self, other):
        try:
            return self.required_fields == other.required_fields
        except AttributeError:
            return False
