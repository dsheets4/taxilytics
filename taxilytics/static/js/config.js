define(['js/3rdparty/ol', 'js/3rdparty/color'], function(ol, color) {

    // TODO: Move the home location information to the database for Organization.
    var home_location_map = {
        KSU: {
            location: [-81.3415601, 41.1448103],
            buffer: 1000
        },
        NycTlc: {
            location: [-73.95000, 40.72000],
            buffer: 10000
        },
        Shenzhen: {
            location: [114.01200, 22.63429],
            buffer: 10000
        },
        Hangzhou: {
            location: [120.22600, 30.24050],
            buffer: 10000
        }
    }

    var config = {}

    config.Home = function(home_name) {
        var home = home_location_map[home_name];
        home.centerPt = new ol.geom.Point(
            ol.proj.transform(home.location, 'EPSG:4326', 'EPSG:3857')
        );
        home.extent = ol.extent.buffer(home.centerPt.getExtent(), home.buffer);
        return home;
    };

    config.colorTbl = new color.ColorTable();

    return config;
});