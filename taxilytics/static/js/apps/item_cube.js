define([
    "js/3rdparty/ol",
    "js/config",
    "js/map/data",
    "js/util",
    "js/apps/cube",
    "js/forms/cubeset_form",
    "js/map/controls/cubeset"
],
function(ol, cfg, data, util, cube, CubesetForm, CubeSetControl) {

    var count = function(cube){
        return cube.count;
    };

    var sum = function(cube){
        return cube.sum;
    };

    var avgSpeed = function(cube) {
        return cube.sum / cube.count;
    }

    var heatValue = avgSpeed;

    var max = -Infinity;
    this.heatScale = function(f) {
        var val = heatValue(f.get("cube"));
        val = ((val*val) / (max*max));
        return val;
    }

    var aggregate = function(o){
        var retObj = {
            "count": 0,
            "sum": 0
        };
        var data = filteredCube[o.getId()]
        if( data ) {
            retObj.count = data.count;
            retObj.sum = data.sum;
        }
        return retObj;
    };

    var systemRegions = new cube.RegionCubeSetLayer({
        title: "System Regions"
    });
    var userRegions = new cube.RegionCubeSetLayer({
        title: "User Regions",
        opacity: 1
    });
    var regionGroup = new ol.layer.Group({
        title: "Region Cube Sets",
        layers: [
            systemRegions.layer,
            userRegions.layer
        ]
    });
    var streetLayer = new cube.StreetLayer();
    var heatLayer = new cube.HeatMapLayer(this.heatScale, {
        threshold_normal: 0.15,
        threshold_invert: 0.80,
    });

    var filteredCube = {};

    var timer_counter = 0;
    function processHeatFeatures(map) {
        var timer = new util.Timer("item_cube.processHeatFeatures");
        // TODO: Creating heatFeatures is duplicated between link and item cubes.
        var heatFeatures = [];
        max = 0;
        var extent = map.getView().calculateExtent(map.getSize());
        streetLayer.layer.getSource().forEachFeature(function(f) {
            var info = f.get("info");
            var newCube = filteredCube[f.getId()];
            if( typeof(newCube) === "undefined" ){
                return;
            }
            var h = heatValue(newCube);
            if( h == 0 ) {
                return;
            }
            max = Math.max(max, isNaN(h) ? -Infinity : h);
            var clone = f.clone();
            clone.set("cube", newCube);
            heatFeatures.push(clone);
        });
        timer.stop();
        if( typeof(benchmarks) !== "undefined" ) {
            console.log("Message ", ++timer_counter, ": Total streets =", heatFeatures.length, ": New max count =", max);
        }
        return heatFeatures;
    }

    function ItemCubeFilterForm(onApply) {
        cube.CubeFilterForm.call(this, onApply);

        var heattype = document.createElement('fieldset');
        var legend = document.createElement("legend");
        legend.innerHTML = "Heatmap Type";
        heattype.appendChild(legend);
        this.heattype_count = document.createElement("input");
        this.heattype_count.type = "radio";
        this.heattype_count.name = "heat_type";
        var label = document.createElement("label");
        label.innerHTML = "Count: ";
        heattype.appendChild(label);
        heattype.appendChild(this.heattype_count);
        this.heattype_speed = document.createElement("input");
        this.heattype_speed.type = "radio";
        this.heattype_speed.name = "heat_type";
        this.heattype_speed.checked = true;
        var label = document.createElement("label");
        label.innerHTML = "Avg Speed: ";
        heattype.appendChild(label);
        heattype.appendChild(this.heattype_speed);
        this.heat_inverted = document.createElement("input");
        this.heat_inverted.type = "checkbox";
        this.heat_inverted.label = "Low to High: ";
        this.heat_inverted.checked = true;

        [heattype, this.heat_inverted].forEach(this.addControl, this);
    }
    ItemCubeFilterForm.prototype = Object.create(cube.CubeFilterForm.prototype);
    ItemCubeFilterForm.prototype.constructor = ItemCubeFilterForm;

    ItemCubeFilterForm.prototype.extendedFields = function(fields) {
        fields.count = this.heattype_count.checked;
        fields.speed = this.heattype_speed.checked;
        fields.invert = this.heat_inverted.checked;
        return fields;
    }

    var filter = new ItemCubeFilterForm(function ItemCubeFilterFormApply(formData) {
        // Reset all filters and regenerate them.
        filters = [];

        if( formData.count ) {
            heatValue = count;
            if( formData.invert ) {
                heatLayer.threshold_max = 0.99;
                heatLayer.threshold_min = 0.80;
            } else {
                heatLayer.threshold_max = 1.00;
                heatLayer.threshold_min = 0.02;
            }
        }
        else if( formData.speed ) {
            heatValue = avgSpeed;
            if( formData.invert ) {
                heatLayer.threshold_max = 0.99;
                heatLayer.threshold_min = 0.90;
            } else {
                // Looks good.
                heatLayer.threshold_max = 1.00;
                heatLayer.threshold_min = 0.20;
            }
        }
        heatLayer.invert = formData.invert;

        if( formData.startdate ) {
            filters.push(new cube[formData.timeMode + "Filter"](formData.startdate, formData.enddate));
        }

        // Filter and update
        filteredCube = {};
        for( let osm in dataObj.cube ) {
            var c = dataObj.cube[osm];
            if( !formData.roadtypes[c.geo.properties.highway].checked ) {
                continue;
            }
            var filteredDetails = {
                counts: [],
                sums: [],
                times: [],
                count: 0,
                sum: 0,
            }
            c.times.forEach(function(t, i) {
                var i, ii = filters.length;
                if( t === null ) {
                    return;
                }
                for( let i = 0; i < ii; i++ ) {
                    if( filters[i].filter(t) ) {
                        return;
                    }
                }
                filteredDetails.times.push(t);
                filteredDetails.counts.push(c.counts[i]);
                filteredDetails.sums.push(c.sums[i]);
                filteredDetails.count += c.counts[i];
                filteredDetails.sum += c.sums[i];
            });
            filteredCube[osm] = filteredDetails;
        }

        // Create the heatmap layer
        var zoomLevel;
        if( this.map ) {
            zoomLevel = this.map.getView().getResolution();
            heatLayer.regenerate(processHeatFeatures(this.map), zoomLevel);
        }
    });

    var timeExtents = [null, null];
    function collectionBuilder(d) {
        for( let osm in d ) {
            d[osm].times.forEach(function(t, i){
                t = util.parseDateTime(t);
                d[osm].times[i] = t;
                if( !timeExtents[0] || t < timeExtents[0] ) {
                    timeExtents[0] = t
                }
                if( !timeExtents[1] || t > timeExtents[1] ) {
                    timeExtents[1] = t
                }
            });
        }
    }

    function buildRegionSet(polygon, operation, name) {
        $.ajax({
            url: initial_data.next[0],
            type: 'POST',
            data: "build_region=" + polygon + "&op=" + operation + "&region_name=" + name,
            headers: {
                "X-CSRFToken": util.getCookie('csrftoken')
            },
            success: function(data, textStatus, jqXHR) {
                dataObj.load(data);
            }
        });
    }

    function requestRegionSet(feature) {
        console.log(
            new Date(),
            "Requesting region set:",
            ((typeof(feature.get("name")) === "undefined" || !feature.get("name")) ? feature.get("id") : feature.get("name"))
        );
        var id = feature;
        if( feature instanceof ol.Feature ) {
            id = feature.get("id");
            if( feature.get("name") ) {
                userRegions.layer.getSource().addFeature(feature);
            }
        } else if( typeof(feature) === "object" ) {
            id = feature.properties.id;
            userRegions.layer.getSource().addFeature(new ol.format.GeoJSON().readFeature(feature));
        } else {
            console.error("Sending region ID only does not support drawing region polygon.");
        }
        dataObj.load({
            next: initial_data.next[0] + "&region_id=" + id
        });
    }

    var cubesetForm, cubesetControl;
    function initApp() {

        cubesetForm = new CubesetForm(
            {
                category: function(c, v) {
                    console.log(new Date(), 'Requesting ' + c + ' cube set ' + v);
                    dataObj.load({
                        next: initial_data.next[0] + "&" + c + "=" + v
                    });
                },
                region: requestRegionSet
            },
            systemRegions.layer, initial_data.next[0]
        );

        var _jsonHandler = function(cubesets, textStatus, jqXHR) {
            // Add the regions to the region layer.
            var systemFeatures = {
                type: "FeatureCollection",
                features: cubesets.regions.features.filter(function(f) {
                    return !f.properties.name;
                }),
                crs: cubesets.regions.crs
            }
            var features = (new ol.format.GeoJSON())
               .readFeatures(systemFeatures, {featureProjection: 'EPSG:3857'});
            console.log("Region Cube Set Features:", features);
            systemRegions.layer.getSource().addFeatures(features);

            // Build the form.
            cubesetForm.addCubeSets(cubesets);
        }
        var url = window.location.href;
        var n = url.lastIndexOf('/');
        url = url.substring(0,n);
        var n = url.lastIndexOf('/');
        url = url.substring(0,n+1) + "cubesets/";
        $.getJSON(url, _jsonHandler);

        cubesetControl = new CubeSetControl({form: cubesetForm.form});
    }

    var dataObj = null;
    function setup() {
        console.log("context", context);
        context.dataObj.args.streetLayer = streetLayer.layer;
        context.dataObj.args.storage = context.db;
        dataObj = new data.Cube(context.dataObj.args);

        dataObj.on("complete", function itemCube_OnComplete() {
            filter.apply();
        });

        // The function here is delayed so that the re-application of the filter is one of
        // the last items to run.  This allows the underlying streets and cube data to be
        // setup first.
        dataObj.on("start", function delayRegister() {
            dataObj.remove("start", delayRegister);
            dataObj.on("data", function itemCube_OnData() {
                filter.timeRange.extents(timeExtents);
                filter.timeRange.selected(timeExtents);
                filter.apply();
            });
        });
    }

    return {
        "info": {
            "header": ["Name", "Count", "Average Speed"],
            "format": function(o){
                var props = o.getProperties();
                var label = ""
                if( props.name ) {
                    label = props.name;
                } else {
                    label = props.highway + "(" + o.getId() + ")";
                }
                var agg = aggregate(o);
                agg.avg_speed = agg.sum / agg.count;
                agg.avg_speed = agg.avg_speed.toFixed(3);
                return [label, agg.count, agg.avg_speed];
            },
        },
        "filterForm": filter,
        "layers": [
            regionGroup,
            streetLayer.layer,
            heatLayer.layer,
        ],
        "getDataObj": function() {
            return dataObj;
        },
        getMapControls: function() {
            if( !cubesetControl ) {
                initApp();
            }
            return [cubesetControl]
        },
        collectionBuilder: collectionBuilder,
        onMapUpdate: function(e, map) {
            // Revise the number of points in the heatmap layer
            switch(e.key) {
                case "resolution":
                    heatLayer.regenerate(processHeatFeatures(map), e.target.get(e.key));
                    break;
                // case "center":
                //    heatLayer.regenerate(processHeatFeatures(map), map.getView().getResolution());
                //    break;
            }
        },
        draw: {
            label: "Region",
            drawend: function(drawnFeature) {
                if( !cubesetForm ) { initApp(); }
                if( cubesetForm.operation === cubesetForm.QueryRegionCommand ) {
                    // Request existing region cube set per user query.
                    var source = systemRegions.layer.getSource();
                    var extent = drawnFeature.getGeometry().getExtent();
                    source.forEachFeatureIntersectingExtent(extent, function(feature) {
                        requestRegionSet(feature);
                    });
                } else {
                    // Draw a new query region and create a cube set.
                    // TODO: Setup so the user can save an area later, after seeing it.
                    var name = prompt("Please enter a name to save the region (leave blank to not save)", "");
                    if( name != null ) {
                        buildRegionSet(
                            new ol.format.WKT().writeFeature(drawnFeature),
                            cubesetForm.operation || "intersects",
                            name
                        );
                    }
                }
            }
        },
        setup: setup
    };
});