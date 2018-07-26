define([
    'js/apps/item_cube',
    'js/apps/link_cube',
    'js/apps/entity',
    'js/apps/osm',
    'js/apps/topic'
],
function(item_cube, link_cube, entity, osm, topic) {
    return {
        "item_cube": item_cube,
        "link_cube": link_cube,
        "entity": entity,
        "osm": osm,
        "topic": topic,
    };
});