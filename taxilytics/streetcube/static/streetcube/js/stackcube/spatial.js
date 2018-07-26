define([
    "streetcube/js/cube/cube_base",
    "ol",
],
function(base, ol) {
    var reader = new ol.format.GeoJSON();

    function SpatialCube(options) {
        base.Cube.call(this, options);

        this.spatial = {};  // The actual cube.
        this.regionSource = new ol.source.Vector();
    }
    SpatialCube.prototype = Object.create(base.Cube.prototype);
    SpatialCube.prototype.constructor = SpatialCube;

    SpatialCube.prototype.temporalExtents = function() {
        let extents = null;
        let localExtents;
        for( let region_id in this.spatial ) {
            var regionCube = this.spatial[region_id];
            if( regionCube.cube ) {
                extents = base.extendTemporalExtents(
                    regionCube.cube.temporalExtents(),
                    extents
                );
            }
        }
        return extents;
    }

    SpatialCube.prototype.mergeSet = function mergeSet(set) {
        var set_id = Object.keys(this.spatial).length;
        this.spatial[set_id] = {
            source: new ol.source.Vector(),
            cube: new this.subCube.cubeType(this.subCube.options)
        };

        var region = this.spatial[set_id];
        for( let street_id in set ) {
            region.source.addFeature(reader.readFeature(set[street_id].geo));
            var subSet = {};
            subSet[street_id] = set[street_id];
            region.cube.mergeSet(subSet);
        }

        var f = new ol.Feature({
            geometry: ol.geom.Polygon.fromExtent(this.spatial[set_id].source.getExtent()),
            name: 'Region: ' + set_id,
        });
        f.setId(set_id);
        this.regionSource.addFeature(f);
    }

    SpatialCube.gValidateTimer = 0;
    SpatialCube.prototype.validateQuery = function validateQuery(q) {
        var t0 = performance.now();

        if( !('regions' in q) || typeof(q.regions) === "undefined" ) {
            console.error("Query error:", q);
            throw "Query must define regions";
        }

        if( (!('extent' in q) || typeof(q.extent) === "undefined") || q.extent.length != 4 ) {
            console.error("Query error:", q);
            throw "Query must define extent as [x1, y1, x2, y2]";
        }

        for( let region_id in q.regions ) {
            var r = q.regions[region_id];
            var regionCube = this.spatial[region_id];
            var regionQuery = q.regions[region_id];
            if( regionCube.cube ) {
                regionCube.cube.validateQuery(regionQuery.subQuery);
            }
        }
        var t1 = performance.now();
        SpatialCube.gValidateTimer += (t1-t0);
        return true;
    }

    SpatialCube.gTimer = 0;
    SpatialCube.prototype.query = function query(q, callback) {
        var t0 = performance.now();
        var result = {};

        // TODO: Add the ability to specifically request a system region for results.
        var coveredRegions = [];
        this.regionSource.forEachFeatureIntersectingExtent(q.extent, function(f) {
            coveredRegions.push(f.getId());
        });

        var jobCounter = coveredRegions.length;
        function mergeSubresult(cube, subResult, aggregate, timing) {
            var t0 = performance.now();
            aggregate = cube.mergeResult(aggregate, subResult);
            if( q.total ) {
                result[null] = cube.mergeResult(result[null], subResult);
            }
            var t1 = performance.now();
            SpatialCube.gTimer += (timing+(t1-t0));
            jobCounter--;
            if( jobCounter == 0 ) {
                callback(result);
            }
        }

        if( this.workers ) {
            for( let i=0; i<this.workers.length; i++ ) {
                this.workers[i].onmessage = function(e) {
                    var subResult = e.data[0];
                    var cube = e.data[1];
                    var aggregate = e.data[2];
                    var timing = e.data[3];
                    mergeSubresult(cube, subResult, aggregate, timing);
                }
            }
        }

        var region_id = 0;
        var mergeFunction;
        for( let i=0; i<coveredRegions.length; i++ ) {
            region_id = coveredRegions[i];
            var regionCube = this.spatial[region_id];
            var regionQuery = q.regions[region_id];
            if( regionCube.cube ) {
                if( !(result[region_id]) ) {
                    result[region_id] = {};
                }
                if( this.workers ) {
                    this.workers[i%this.workers.length].postMessage(
                        [regionCube.cube, regionQuery.subQuery, result[region_id]]
                    );
                } else {
                    var t0 = performance.now();
                    subResult = this._subquery(
                        regionCube.cube,
                        regionQuery.subQuery,
                        result[region_id]
                    );
                    var t1 = performance.now();
                    mergeSubresult(regionCube.cube, subResult, result[region_id], (t1-t0));
                }
            }
        }
        return result;
    }

    SpatialCube.prototype.mergeResult = function(target, input) {
        console.error("SpatialCube.mergeResult not implemented:", target, input);

        return target;
    }

    return SpatialCube;
});