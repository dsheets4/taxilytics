
define([
    "streetcube/js/cube",
    "js/util",
],
function(cube, util) {
    var model = {};

    function createQueryStreet(template, cubeObj, query) {

    }

    function createQuerySpatial(template, cubeObj, query) {
        if( !(cubeObj instanceof cube.SpatialCube) ) {
            console.error("Incorrect cube type in createQuerySpatial:", cubeObj.constructor);
            return query;
        }

        query.regions = {};
        query.extent = template.SpatialCube.extent;
        query.group = template.SpatialCube.group;
        if( typeof(template.SpatialCube.total) !== "undefined" ) {
            query.total = template.SpatialCube.total;
        }

        for( let region_id in cubeObj.spatial ) {
            query.regions[region_id] = {};
            var regionQuery = query.regions[region_id];

            var regionCube = cubeObj.spatial[region_id].cube;
            if( regionCube ) {
                regionQuery.subQuery = createQuery(template, regionCube, {});
                if( query.total && !query.merge ) {
                    query.merge = regionCube;
                }
            }
        }
        return query;
    }

    function createQueryTemporal(template, cubeObj, query) {
        if( !(cubeObj instanceof cube.TemporalCube) ) {
            console.error("Incorrect cube type in createQueryTemporal:", cubeObj.constructor);
            return query;
        }

        query.indexer = template.TemporalCube.indexer;
        query.extents = template.TemporalCube.extents;

        if( cubeObj.subCube ) {
            query.subQuery = createQuery(template, cubeObj.subCube, {});
            if( query.total && !query.merge ) {
                query.merge = cubeObj.subCube;
            }
        }
        return query;
    }

    function createQueryCategorical(template, cubeObj, query) {
        if( !(cubeObj instanceof cube.CategoricalCube) ) {
            console.error("Incorrect cube type in createQueryCategorical:", cube.constructor);
            return query;
        }

        query.categories = {};
        for( let cat in template.CategoricalCube.categories ) {
            query.categories[cat] = {};
            var category = template.CategoricalCube.categories[cat];
            var catQuery = query.categories[cat];
            var catCube = cubeObj.categorical[cat];

            catQuery.values = category.values;
            for( var v in catCube.values ) {
                var value = catCube.values[v];
                if( value.cube ) {
                    catQuery.subQuery = createQuery(template, value.cube, {});
                    if( query.total && !query.merge ) {
                        query.merge = value.cube;
                    }
                }
            }
        }
        if( template.CategoricalCube.total ) {
            query.total = template.CategoricalCube.total;
        }
        return query;
    }

    function createQuery(template, cube) {
        switch( cube.constructor.name ) {
            case "SpatialCube":
                return createQuerySpatial(template, cube, {});
            case "TemporalCube":
                return createQueryTemporal(template, cube, {});
            case "CategoricalCube":
                return createQueryCategorical(template, cube, {});
        }
    }

    // ------------------------------------------------------------------------
    function CubeModelCommand(cube, queryTemplate) {
        console.log("Creating ModelCommand", cube, queryTemplate)
        util.Emitter.call(this);
        this._queryTemplate = queryTemplate;
        this.cube(cube);
        this.processing = false;

        this.events = {
            "update": new util.EventObject(),
        };
    }
    CubeModelCommand.prototype = Object.create(util.Emitter.prototype);
    CubeModelCommand.prototype.constructor = CubeModelCommand;

    CubeModelCommand.prototype.createAndValidate = function() {
        var theCube = this.cube();
        if( theCube ) {
            this.query = createQuery(this._queryTemplate, theCube);
            if( this.isTemplateValid() ) {
                theCube.validateQuery(this.query);
            }
        }
    }

    CubeModelCommand.prototype.isTemplateValid = function(cube) {
        return (
            this._queryTemplate.TemporalCube.extents &&
            this._queryTemplate.SpatialCube.extent
        );
    }

    CubeModelCommand.prototype.cube = function(cube) {
        if( typeof(cube) !== "undefined" ) {
            this._cube = cube;
            if( this.isTemplateValid() ) {
                this.createAndValidate();
            }
        } else {
            return this._cube;
        }
    }

    CubeModelCommand.prototype.timeExtents = function(extents) {
        var theCube = this.cube();
        this._queryTemplate.TemporalCube.extents = extents;
        this.createAndValidate();
        return this;
    }

    CubeModelCommand.prototype.categoryValues = function(category, values) {
        var theCube = this.cube();
        this._queryTemplate.CategoricalCube.categories[category].values = values;
        this.createAndValidate();
        return this;
    }

    CubeModelCommand.prototype.rangeExtents = function(extent) {
        var theCube = this.cube();
        this._queryTemplate.SpatialCube.extent = extent;
        this.createAndValidate();
        return this;
    }

    CubeModelCommand.prototype.execute = function() {
        var theCube = this.cube();
        if( !this.processing && theCube && this.isTemplateValid() ) {
            var self = this;
            var emitter = function(result) {
                self.processing = false;
                self.emit("update", result);
            }
            this.processing = true;
            this.cube().query(this.query, emitter);
        }
        return this;
    }


    // ------------------------------------------------------------------------
    function CubeModel() {
        util.Emitter.call(this);
        this.cube = null;

        this.events = {
            "loaded": new util.EventObject(),
        };
    }
    CubeModel.prototype = Object.create(util.Emitter.prototype);
    CubeModel.prototype.constructor = CubeModel;

    CubeModel.prototype.create = function(cubeConfig, callback) {
        this.config = cubeConfig;
        var self = this;
        self.cube = null;

        cube.getAvailableSets(function(cubeSets) {
            console.log("Available cube sets:", cubeSets);
            self.cubeSets = cubeSets;
            if( typeof(callback) === "function" ) {
                callback(self.cubeSets);
            }
        });
    };

    CubeModel.prototype.requestData = function(chooseSet) {
        chooseSet = chooseSet || function(cubesets) {
            return cubesets.regions.system.features;
        }
        var self = this;
        var cubeRequestRef = chooseSet(self.cubeSets);
        cube.requestCubeSet(
            cubeRequestRef,
            self.config,
            {
                done: function(c) {
                    self.cube = c;
                    self.emit("loaded", [self.cube]);
                },
                setLoaded: function(data, loaded, total) {
                    console.log("Loaded " + loaded + " of " + total + " sets.", data);
                }
            },
            self.cube
        );
    };

    CubeModel.prototype.command = function(query) {
        var command = new CubeModelCommand(this.cube, query);
        this.on("loaded", command.cube, command);
        return command;
    }

    CubeModel.prototype.getRegionSource = function() {
        // TODO: The top-level cube won't always be spatial.
        return this.cube.regionSource;
    }

    CubeModel.prototype.getStreetSources = function() {
        // TODO: The top-level cube won't always be spatial.
        var sources = [];
        for( let region_id in this.cube.spatial ) {
            sources.push(this.cube.spatial[region_id].source);
        }
        return sources;
    }

    model.CubeModel = CubeModel;
    return model;
});