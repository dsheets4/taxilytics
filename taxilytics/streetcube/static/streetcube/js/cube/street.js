define([
    "js/util",
    "streetcube/js/cube/cube_utils",
    "streetcube/js/cube/cube_base",
],
function(util, cube_utils, base) {

    function StreetCube(options) {
        base.Cube.call(this, options);
        this.streets = {};
    }
    StreetCube.prototype = Object.create(base.Cube.prototype);
    StreetCube.prototype.constructor = StreetCube;

    StreetCube.prototype.mergeSet = function(set) {
        for( let s_id in set ) {
            var street = set[s_id];
            this.streets[s_id] = this.merge(this.streets[s_id], street);
        }
    }


    StreetCube.prototype.validateQuery = function(q) {
        if( q && 'streets' in q ) {
            if( !(q.streets instanceof Array) ) {
                console.error("Query error:", q);
                throw "StreetCube query must include list of street IDs or be empty";
            }
        }
    }


    StreetCube.prototype.query = function(q, callback) {
        if( streets in g ) {
            var retVal = {};
            for( let s_id of q.streets ) {
                retVal[s_id] = this.streets[s_id];
            }
            return retVal;
        }
        return this.streets;
    }


    StreetCube.prototype.getAggregate = function() {
        var aggMetrics;
        for( let s_id in this.streets ) {
            var street = this.streets[s_id];
            aggMetrics = this.merge(aggMetrics, street);
        }
        aggMetrics.streets = this.streets;
        return aggMetrics;
    }


    StreetCube.prototype.mergeResult = function(target, input) {
        if( typeof(target) === "undefined" ) {
            target = {};
        }

        for( let s_id in input ) {
            target[s_id] = this.merge(target[s_id], input[s_id]);
        }
        return target;
    }

    return StreetCube;
});