define(['ol'], function(ol) {
    var mouse = {};

    var precision = 4;
    mouse.posToLatLon = function(coordinate) {
        var lonlat = ol.proj.transform(coordinate, 'EPSG:3857', 'EPSG:4326');
        return "(" + lonlat[1].toFixed(precision) + "," + lonlat[0].toFixed(precision) + ")";
    }

    return mouse;
});