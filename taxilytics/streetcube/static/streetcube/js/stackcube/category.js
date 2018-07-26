define([
    "streetcube/js/cube/cube_base",
],
function(base) {

    function CategoricalCube(options) {
        base.Cube.call(this, options);

        // Stores the hierarachy as top-level keys and hierarchy values as array.
        this.hierarchy = {};
        if( options.hierarchy ) {
            for( let i=0; i < options.hierarchy.length; i++ ) {
                this.hierarchy[options.hierarchy[i]] = {};
            }
        } else {
            console.error("CategoricalCube requires at least one hierarchy level.")
        }

        this.categorical = {};  // The actual cube.
    }
    CategoricalCube.prototype = Object.create(base.Cube.prototype);
    CategoricalCube.prototype.constructor = CategoricalCube;

    CategoricalCube.prototype.temporalExtents = function() {
        let extents = null;
        let localExtents;
        for( let cat in this.categorical ) {
            for( let value in this.categorical[cat].values ) {
                extents = base.extendTemporalExtents(
                    this.categorical[cat].values[value].cube.temporalExtents(),
                    extents
                );
            }
        }
        return extents;
    }

    CategoricalCube.prototype.mergeSet = function mergeSet(set) {
        var level;
        var hierarchyValue = Object.keys(this.hierarchy);
        var cat, value;
        for( let s_id in set) {
            level = this.categorical;
            var street = set[s_id];
            this.template = base.createMetricTemplate(street);
            this.templateStr = JSON.stringify(this.template);

            for( let i=0; i < hierarchyValue.length; i++ ) {
                cat = hierarchyValue[i];
                value = this.accessor(set[s_id], cat);
                if( !(value in this.hierarchy[cat]) ) {
                    this.hierarchy[cat][value] = 0;  // TODO: Set this to a rollup.
                }
                this.hierarchy[cat][value]++;

                if( !(cat in level) ) {
                    level[cat] = {
                        values: {},
                        agg: JSON.parse(this.templateStr)
                    };
                }
                this.merge(level[cat].agg, street);
                if( !(value in level[cat].values) ) {
                    level[cat].values[value] = {
                        values: {},
                        agg: JSON.parse(this.templateStr)
                    };
                }
                this.merge(level[cat].values[value].agg, street);
                level = level[cat].values[value];
            }
            // TODO: The aggregates for the categorical cube should come from the sub-cube
            // Create the next level cube and send data down.
            if( !(level.cube instanceof this.subCube.cubeType) ) {
                level.cube = new this.subCube.cubeType(this.subCube.options);
            }
            var subSet = {};
            subSet[s_id] = street;
            level.cube.mergeSet(subSet);
        }
    }

    CategoricalCube.gValidateTimer = 0;
    CategoricalCube.prototype.validateQuery = function(q) {
        var t0 = performance.now();
        var queryValues = Object.keys(q.categories);
        for( let i=0; i<queryValues.length; i++ ) {
            if( !(queryValues[i] in this.categorical) ) {
                throw "Cube does not contain category " + queryValues[i];
            }
        }
        for( var cat in q.categories ) {
            var catQuery = q.categories[cat];
            if( catQuery.values ) {
                for( let i=0; i<catQuery.values.length; i++ ) {
                    var val = catQuery.values[i];
                    if( val in this.categorical[cat].values ) {
                        this.categorical[cat].values[val].cube.validateQuery(catQuery.subQuery);
                    }
                }
            }
        }
        var t1 = performance.now();
        CategoricalCube.gValidateTimer += (t1-t0);
        return true;
    }

    CategoricalCube.gTimer = 0;
    CategoricalCube.prototype.query = function(q, callback) {
        var t0 = performance.now();
        var result = {};
        for( var cat in q.categories ) {
            var catQuery = q.categories[cat];
            var catCube = this.categorical[cat];
            result[cat] = {};
            if( !catQuery.values ) {
                if( !catQuery.subQuery ) {
                    console.log("CategoricalCube no query values, returning aggregate.")
                    result[cat][null] = [catCube.agg];
                } else {
                    result[cat] = {};
                    for( var v in catCube.values ) {
                        var valueCube = catCube.values[v];
                        var t1 = performance.now();
                        CategoricalCube.gTimer += (t1 - t0);
                        var subResult = valueCube.cube.query(catQuery.subQuery);
                        var t0 = performance.now();
                        result[cat][null] = valueCube.cube.mergeResult(result[cat][null], subResult);
                    }
                }
            } else {
                for( let i=0; i<catQuery.values.length; i++ ) {
                    var value = catQuery.values[i];
                    if( value in catCube.values ) {
                        var valueCube = catCube.values[value];
                        if( !catQuery.subQuery ) {
                            var t1 = performance.now();
                            CategoricalCube.gTimer += (t1 - t0);
                            result[cat][value] = [valueCube.cube.query(null)];
                            var t0 = performance.now();
                        } else {
                            var t1 = performance.now();
                            CategoricalCube.gTimer += (t1 - t0);
                            result[cat][value] = valueCube.cube.query(catQuery.subQuery);
                            var t0 = performance.now();
                        }
                        if( q.total ) {
                            result[cat][null] = valueCube.cube.mergeResult(result[cat][null], result[cat][value]);
                        }
                    } else {
                        //result[cat][value] = [JSON.parse(this.templateStr)];
                    }
                }
            }
        }
        var t1 = performance.now();
        CategoricalCube.gTimer += (t1 - t0);
        return result;
    }

    CategoricalCube.prototype.mergeResult = function(target, input) {
        if( typeof(target) === "undefined" ) {
            target = {};
        }
        for( let cat in input ) {
            if( !(cat in target) ) {
                target[cat] = {};
            }
            var catCube = this.categorical[cat];
            var oCategory = target[cat];
            var iCategory = input[cat];
            var lastValueCube = null;
            var calcTotal = null;
            for( let val in iCategory ) {
                var iValue = iCategory[val];
                if( val == "null" ) {
                    // It's the total.
                    if( !lastValueCube ) {
                        // TODO: This is NOT a good way to calculate the total of the categories
                        //       Different categories can have different subordinate cubes but
                        //       within a category the subordinate cube is the same.  Therefore,
                        //       there should be a cube type associated with each and mergeResult
                        //       doesn't require a this context and can be a 'class' method.
                        calcTotal = (function(input, output, val) {
                            return function() {
                                output[val] = lastValueCube.cube.mergeResult(output[val], input)
                            }
                        })(iValue, oCategory, val);
                    } else {
                        oCategory[val] = lastValueCube.cube.mergeResult(oCategory[val], iValue);
                    }
                } else {
                    var valueCube = catCube.values[val];
                    oCategory[val] = valueCube.cube.mergeResult(oCategory[val], iValue);
                    lastValueCube = valueCube;
                }
            }
        }
        return target;
    }

    return CategoricalCube;
});