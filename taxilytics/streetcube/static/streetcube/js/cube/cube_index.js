define([
    "streetcube/js/cube/street",
    "streetcube/js/cube/temporal",
    "streetcube/js/cube/categorical",
    "streetcube/js/cube/spatial",
],
function(StreetCube, TemporalCube, CategoricalCube, SpatialCube) {
    var cube = {
        StreetCube: StreetCube,
        TemporalCube: TemporalCube,
        CategoricalCube: CategoricalCube,
        SpatialCube: SpatialCube,
    };


    function getUrl() {
        var url = window.location.href;
        var n = url.lastIndexOf('/');
        url = url.substring(0,n);
        var n = url.lastIndexOf('/');
        return url.substring(0,n+1) + "trajcube/";
    }

    function split_region_sets(regions) {
        function applyRegionFilter(filter) {
            return {
                type: "FeatureCollection",
                features: regions.features.filter(filter),
                crs: regions.crs
            };
        };
        return {
            system: applyRegionFilter(function(f) {
                return f.properties.sys;
            }),
            user: applyRegionFilter(function(f) {
                return !f.properties.sys;
            })
        }
    }


    cube.getAvailableSets = function get_available_sets(handler) {
        url = getUrl() + "cubesets/";
        $.getJSON(url, function(cubeSets, status, jqXHR) {
            handler({
                regions: split_region_sets(cubeSets.regions),
                categories: cubeSets.categories
            });
        });
    }

    cube.requestCubeSet = function request_cube_set(setRef, config, callbacks, theCube) {
        if( typeof(callbacks) === "undefined" ) {
            callbacks = {};
        }
        console.log("Creating cube with configuration:", config);
        if( !theCube ) {
            theCube = new config.cubeType(config.options);
        }
        var pendingSets = 0;
        var totalSets = 0;

        function requestSetByUrl(url) {
            pendingSets++;
            totalSets++;
            $.getJSON(url, function(data, status, jqXHR) {

                // TODO: Cache data locally.

                pendingSets--;
                if( data.next ) {
                    requestSetByUrl(data.next);
                }
                theCube.mergeSet(data.results);
                if( callbacks.setLoaded ) {
                    callbacks.setLoaded(data.results, totalSets-pendingSets, totalSets);
                }

                if( pendingSets == 0 && callbacks.done ) {
                    callbacks.done(theCube);
                }
            });
        }
        function requestSet(set) {
            if( typeof(set.type) !== "undefined" && set.type == "Feature" ) {
                requestSetByUrl(getUrl() + "st/?cube_type=street&region_id=" + set.properties.id);
            } else {
                console.log("TODO: Setup for requesting categorical sets.");
            }
        }

        if( setRef instanceof Array ) {
            setRef.forEach(requestSet)
        } else if( typeof(setRef.type) !== "undefined" && setRef.type === "FeatureCollection" ) {
            setRef.features.forEach(requestSet);
        } else {
            requestSet(setRef);
        }
    }


    cube.requestCategorySet = function request_category_set(cat) {
    }


    return cube;
});