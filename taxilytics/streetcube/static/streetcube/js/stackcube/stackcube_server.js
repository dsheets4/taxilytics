define([
],
function() {
    /* Sever provides interfaces to the server including the ability to cache data. */
    /**
     Download the available set references.  A set reference contains the spatial, category,
     and temporal information required to set up the user interfaces.
       * Spatial - Provides region geometries
       * Category - Provides the name of the category and the values
       * Temporal - Provides the range of times containing data
    */

    var server = {
    };


    function get_url() {
        var url = window.location.href;
        var n = url.lastIndexOf('/');
        url = url.substring(0,n);
        var n = url.lastIndexOf('/');
        return url.substring(0,n+1) + "trajcube/";
    }

    function split_region_sets(regions) {
        function region_filter(filter) {
            return {
                type: "FeatureCollection",
                features: regions.features.filter(filter),
                crs: regions.crs
            };
        };
        return {
            system: region_filter(function(f) {
                return f.properties.sys;
            }),
            user: region_filter(function(f) {
                return !f.properties.sys;
            })
        }
    }


    server.get_available_sets = function get_available_sets(handler) {
        url = get_url() + "cubesets/";
        $.getJSON(url, function(cube_sets, status, jqXHR) {
            handler({
                regions: split_region_sets(cube_sets.regions),
                categories: cube_sets.categories
            });
        });
    }

    cube.request_set = function request_cube_set(set_ref, config, callbacks, the_cube) {
        if( typeof(callbacks) === "undefined" ) {
            callbacks = {};
        }
        console.log("Creating cube with configuration:", config);
        if( !the_cube ) {
            the_cube = new config.cubeType(config.options);
        }
        var pending_sets = 0;
        var total_sets = 0;

        function request_set(url) {
            pending_sets++;
            total_sets++;
            $.getJSON(url, function(data, status, jqXHR) {

                // TODO: Cache data locally.

                pending_sets--;
                if( data.next ) {
                    request_set(data.next);
                }
                the_cube.mergeSet(data.results);
                if( callbacks.setLoaded ) {
                    callbacks.setLoaded(data.results, total_sets-pending_sets, total_sets);
                }

                if( pending_sets == 0 && callbacks.done ) {
                    callbacks.done(the_cube);
                }
            });
        }
        function requestSet(set) {
            if( typeof(set.type) !== "undefined" && set.type == "Feature" ) {
                request_set(getUrl() + "st/?cube_type=street&region_id=" + set.properties.id);
            } else {
                console.log("TODO: Setup for requesting categorical sets.");
            }
        }

        if( set_ref instanceof Array ) {
            set_ref.forEach(requestSet)
        } else if( typeof(set_ref.type) !== "undefined" && set_ref.type === "FeatureCollection" ) {
            set_ref.features.forEach(requestSet);
        } else {
            requestSet(set_ref);
        }
    }


    return server;
});