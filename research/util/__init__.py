import logging


logger = logging  # NOQA


from .general import (
    OptionsCache,
    default_args,
    update_dict, dict_combiner,
    filter_kwargs, option_list,
    haversine,
    make_enum,
    create_dir,
    heading_delta,
    sort_nicely,
    grouper,
    load_item,
)

from .colortable import (
    get_color_string,
    get_color_string_rgb,
    get_color_string_rgba
)

# TODO: Figure out how to reliably get PyQt4 installed on the server.
# from .web import dict_to_ul, Screenshot
