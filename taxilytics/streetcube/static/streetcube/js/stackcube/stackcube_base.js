define([
],
function() {
    var base = {};

    base.createMetricTemplate = function createMetricTemplate(d) {
        var template = {};
        for( var prop in d ) {
            if( prop != "times" && prop != "geo" ) {
                template[prop] = 0;
            }
        }
        return template;
    }

    base.Cube = function Cube(options) {
        //console.log(this.constructor.name, "created with options", options);
        options = options || {};
        this.options = JSON.parse(JSON.stringify(options));
        if( options.workers ) {
            this.workers = [];
            for( let i=0; i<this.options.workers; i++ ) {
                // TODO: Will probably need to inject URL as context into the HTML template via django.
                var worker = new Worker(
                    window.location.origin + '/static/streetcube/js/cube/cube_worker.js'
                );
                this.workers.push(worker);
            }
        }

        // Function to get hierarchy value from object.
        this.accessor = options.accessor;

        // Function to merge individual results into pre-aggregation.
        this.merge = options.merge;

        // Type of cube to create subordinate to this one.
        this.subCube = options.subordinateCube;
    }
    base.Cube.prototype = Object.create(Object.prototype);
    base.Cube.prototype.constructor = base.Cube;

    base.Cube.prototype._subquery = function(cube, query, result) {
        // Basically duplicated logic from cube_worker.js
        var t0 = performance.now();
        var subResult = cube.query(query);
        return subResult;
    }

    base.extendTemporalExtents = function(localExtents, extents) {
        if( localExtents[0] > localExtents[1] ) {
            console.error("localExtents reversed", localExtents)
        }
        if( !extents ) {
            extents = localExtents;
        } else {
            if( extents[0] > localExtents[0] ) {
                extents[0] = localExtents[0];
            }
            if( extents[1] < localExtents[1] ) {
                extents[1] = localExtents[1];
            }
        }
        return extents;
    }

    return base;
});