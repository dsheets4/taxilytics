requirejs.config({
	// By default load any module IDs from path:
	// TODO: Static is a hardcoded variable that should come from server framework
	baseUrl : '/static',

	// paths: When a request for the key comes in, look in value instead.
	paths: {
	    "ol": "js/3rdparty/ol-debug",
	    "Chart": "js/3rdparty/Chart.bundle",
	},
	shim: {
        "ol": {
            "exports": "ol"
        },
	},
	packages: [
	    {name: 'js/map/controls', main: 'index'},
	    {name: 'streetcube/js/cube', main: 'cube_index'},
	    {name: 'streetcube/js/vis', main: 'vis_index'},
	]
});


debug = true;


require([
    "streetcube/js/cube",
    "streetcube/js/cube-model",
    "streetcube/js/cube-view",
],
function(cube, model, view) {

    // Hangzhou
    //var spatialExtent = [
    //    120.11727839938355, 30.264608441503327,
    //    120.14049560061648, 30.272021418561692
    //];
    // NYC
    var spatialExtent = [
        -74.041290, 40.762594,
        -73.963785, 40.738341
    ];
    var highwayValues = [
        'motorway',
        'trunk',
        'primary',
        'secondary',
    ];
    var possibleHighwayValues = [
        'total',
        'motorway',
        'trunk',
        'primary',
        'secondary',
        'tertiary',
        'unclassified',
        'residential',
        'service',
        'motorway_link',
        'trunk_link',
        'primary_link',
        'secondary_link',
        'tertiary_link',
        'living_street',
        'road',
        // 'turning_circle'
    ];

    var myView = new view.CubeView();
    var myModel = new model.CubeModel();
    var summary = myModel.command({
        TemporalCube: {
            indexer: new cube.TemporalCube.indexers.Indexer({
                cell: 60 * 60 * 24,
            })
        },
        CategoricalCube: {
            categories: {
                highway: {
                    values: highwayValues,
                },
            },
            total: true
        },
        SpatialCube: {
            extents: spatialExtent,
            total: true
        },
        StreetCube: {},
    });
    var hourly = myModel.command({
        TemporalCube: {
            indexer: new cube.TemporalCube.indexers.HourOfDay()
        },
        CategoricalCube: {
            categories: {
                highway: {
                    values: highwayValues,
                },
            },
            total: true
        },
        SpatialCube: {
            extents: spatialExtent,
            total: true
        },
        StreetCube: {},
    });
    var daily = myModel.command({
        TemporalCube: {
            indexer: new cube.TemporalCube.indexers.DayOfWeek()
        },
        CategoricalCube: {
            categories: {
                highway: {
                    values: highwayValues,
                },
            },
            total: true
        },
        SpatialCube: {
            extents: spatialExtent,
            total: true
        },
        StreetCube: {
            merge: function mergeStreet(s1, s2) {
            }
        },
    });

    function getStartExtent(d) {
        return d.extents[0];
    }

    function avgSpeed(d) {
        return d.sums / d.counts;
    }

    function avgDistance(d) {
        return d.dist_sum / d.cnt;
    }

    function avgFare(d) {
        return d.fare_sum / d.cnt;
    }

    function avgPassengers(d) {
        return d.pass_sum / d.cnt;
    }

    var chartMetric = avgFare;

    function count(d) {
        return d.counts;
    }

    var bgColorTable = [
        'rgba(255,  99, 132, 0.2)',
        'rgba( 54, 162, 235, 0.2)',
        'rgba(255, 206,  86, 0.2)',
        'rgba( 75, 192, 192, 0.2)',
        'rgba(153, 102, 255, 0.2)',
        'rgba(255, 159,  64, 0.2)'
    ];
    var bdColorTable = [
        'rgba(255,  99, 132, 0.8)',
        'rgba( 54, 162, 235, 0.8)',
        'rgba(255, 206,  86, 0.8)',
        'rgba( 75, 192, 192, 0.8)',
        'rgba(153, 102, 255, 0.8)',
        'rgba(255, 159,  64, 0.8)'
    ];

    function generateData(result, dataFunc, timeFunc) {
        var data = {
            datasets: [],
        }
        var xData = null;
        var regionData = result[null];  // Pre-merged results.
        for( let cat in regionData ) {
            var i = 0;
            var catData = regionData[cat];
            var chartType;
            var dataLabel = 'The Label';
            for( let val in catData ) {
                chartType = 'line';
                if( val == "null" ) {
                    dataLabel = "total";
                    chartType = 'bar';
                } else {
                    dataLabel = val;
                    if( !data.labels && timeFunc ) {
                        data.labels = catData[val].map(timeFunc);
                    }
                }
                var dTmp = catData[val].map(dataFunc);
                data.datasets.push({
                    label: dataLabel,
                    data: dTmp,
                    type: chartType,
                    fill: false,
                    backgroundColor: bgColorTable[i],
                    borderColor: bdColorTable[i],
                });
                i++;
            }
        }
        return data;
    }

    function updateView(name, dataFunc, timeFunc) {
        var chart = myView[name];
        var name = "updateView(" + (name || "") + ") time(ms)->";
        function display(n) { return parseFloat(n.toFixed(3)); }
        return function(result) {
            var t0 = performance.now();
            var data = generateData(result, dataFunc, timeFunc);
            var t1 = performance.now();
            chart.load(data);
            //chart.visibleColumns(data.map(function(d) {
            //    return d[0];
            //}));
            var t2 = performance.now();

            console.log(name,
                "Grand Total:", display(
                    (t2-t0) +
                    cube.SpatialCube.gTimer+cube.CategoricalCube.gTimer+cube.TemporalCube.gTimer
                ),
                "; query.Total:", display(
                    cube.SpatialCube.gTimer+cube.CategoricalCube.gTimer+cube.TemporalCube.gTimer
                ),
                "; vis total:", display((t2-t0)),
                "; query.Spatial:", display(cube.SpatialCube.gTimer),
                "; query.Categorical:", display(cube.CategoricalCube.gTimer),
                "; query.Temporal:", display(cube.TemporalCube.gTimer),
                "; vis.generateData:", display((t1-t0)),
                "; vis.load:", display((t2-t1)),
            );
            cube.SpatialCube.gTimer = 0;
            cube.CategoricalCube.gTimer = 0;
            cube.TemporalCube.gTimer = 0;
        }
    }

    function updateTimeExtents(extents) {
        summary
            .timeExtents(extents)
            .execute();
        hourly
            .timeExtents(extents)
            .execute();
        daily
            .timeExtents(extents)
            .execute();
    }

    // TODO: This needs converted to a function that just sets the chart data.
    myModel.on("loaded", function(cube) {
        console.log("Cube loaded:", cube);
        updateTimeExtents([cube.temporalExtents()]);
        // System region squares are added entirely before downloading data.
        //myView.map.addSource(myModel.getRegionSource(), "region", "System Regions");
        var i = 0;
        myView.heatLayer.clear();
        myModel.getStreetSources().forEach(function(s) {
            myView.map.addSource(s, "street", "Streets: " + (i++));
            myView.heatLayer.setSource(s);
        });
        myView.heatLayer.regenerate(myView.map.getView().getResolution());
    });

    function createTimeSelectHandler(kind) {
        return function timeSelectHandler(extents) {
            extents = [extents];
            hourly
                .timeExtents(extents, kind)
                .execute();
            daily
                .timeExtents(extents, kind)
                .execute();
        }
    }
    myView.on("timeSelectAbsolute", createTimeSelectHandler('absolute'));
    myView.on("timeSelectDays", createTimeSelectHandler('days'));
    myView.on("timeSelectHours", createTimeSelectHandler('hours'));

    myView.on("categorySelection", function categorySelection(selData) {
        for( let cat in selData ) {
            for( let val in selData[cat] ) {
                if( val == "total" ) {
                    continue;
                }
                var catVal = selData[cat][val];
                if( catVal ) {
                    if( highwayValues.indexOf(val) == -1 ) {
                        highwayValues.push(val);
                    }
                } else {
                    let idx = highwayValues.indexOf(val);
                    if( idx > -1 ) {
                        highwayValues.splice(idx, 1);
                    }
                }
            }
            if( highwayValues.length == 0 ) {
                summary.categoryValues(cat, null);
                hourly.categoryValues(cat, null);
                daily.categoryValues(cat, null);
            } else {
                summary.categoryValues(cat, highwayValues);
                hourly.categoryValues(cat, highwayValues);
                daily.categoryValues(cat, highwayValues);
            }
        }
        summary.execute();
        hourly.execute();
        daily.execute();
    });

    myView.on("userSelection", function userSelection(features) {
        myModel.requestData(function() {
            return features;
        });
    });

    myView.on("regionSelection", function regionSelection(extent) {
        summary
            .rangeExtents(extent)
            .execute();
        hourly
            .rangeExtents(extent)
            .execute();
        daily
            .rangeExtents(extent)
            .execute();
    });

    function mergeProp(tgt, src, prop) {
        if( prop in src ) {
            if( src[prop] ) {
                tgt[prop] += (+src[prop]);
            } else {
                tgt[prop] = (+src[prop]);
            }
        }
    }

    function dataMerge(res, add) {
        // TODO: Temporal cube still doing specifics about the data, should be here
        if( !res ) {
            res = Object.assign({}, add);
        } else {
            mergeProp(res, add, "cnt");
            mergeProp(res, add, "sums");
            mergeProp(res, add, "dist_sum");
            mergeProp(res, add, "fare_sum");
            mergeProp(res, add, "pass_sum");
        }
        return res;
    }

    function catMergeResult(res, add) {
        for( let prop in add ) {
            if( prop == "geo" || prop == "times" ) { continue; }
            res[prop] += add[prop].reduce(function(acc, val) {
                return acc + val;
            });
        }
    }

    var cubeConfig = {
        cubeType: cube.SpatialCube,
        options: {
            subordinateCube: {
                cubeType: cube.CategoricalCube,
                options: {
                    subordinateCube: {
                        cubeType: cube.TemporalCube,
                        options: {
                            subordinateCube: {
                                cubeType: cube.StreetCube,
                                options: {
                                    merge: dataMerge
                                }
                            },
                            merge: dataMerge
                        },
                    },
                    hierarchy: ['highway'],
                    accessor: function(d, hierarchy) {
                        return d.geo.properties[hierarchy];
                    },
                    merge: catMergeResult,
                }
            },
            //workers: 4,
        }
    };


    $(function run() {
        myView.create();
        myView.map.setViewExtent(spatialExtent, "EPSG:4326");
        myView.setAvailableCategoryValues(possibleHighwayValues);
        myView.setInitialCategoryValues(highwayValues);
        summary.on("update", updateView("summary", chartMetric, getStartExtent));
        daily.on("update", updateView("daily", chartMetric));
        hourly.on("update", updateView("hourly", chartMetric));
        myModel.create(cubeConfig, function(cubesets) {
            regionSource = myView.map.createSourceFromFeatures(cubesets.regions.system);
            myView.map.addSource(regionSource, "region", "System Regions");
            myView.map.createFeatureSelector(regionSource, null);

            regionSource = myView.map.createSourceFromFeatures(cubesets.regions.user);
            myView.map.addSource(regionSource, "region", "User Regions");
            // myView.map.createFeatureSelector(regionSource, null);

//            myModel.requestData(function chooseFeatures(cubesets) {
//                // Based on default NYC view extents
//                return [].concat(
//                    cubesets.regions.system.features.slice(10,11),
//                ); // Small test
//            });
        });
    });
});