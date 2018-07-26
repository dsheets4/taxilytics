from django.core.exceptions import ValidationError

from django.utils.deconstruct import deconstructible


from util.general import (
    filter_kwargs
)


@deconstructible
class CallableArgumentValidator(object):

    def __init__(self, call_obj):
        self.call_obj = call_obj

    def __call__(self, kwargs):
        _, bad_args, _ = filter_kwargs(self.call_obj, kwargs)
        if len(bad_args) > 0:
            raise ValidationError(
                'Arguments not supported by the callable: {}'.format(
                    ','.join(bad_args)
                ))

    def __eq__(self, other):
        if isinstance(other, CallableArgumentValidator):
            return self.call_obj == other.call_obj

        return NotImplemented
