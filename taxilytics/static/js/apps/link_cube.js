define(["js/3rdparty/ol", "js/config", "js/map/data", "js/util", "js/apps/cube"],
function(ol, cfg, data, util, cube) {

    var pickupCountFunction = function(cube){
        if( cube.pick ) {
            return cube.pick.count;
        }
        return 0;
    };

    var dropoffCountFunction = function(cube){
        if( cube.drop ) {
            return cube.drop.count;
        }
        return 0;
    };

    var heatValue = pickupCountFunction;

    var max = -Infinity;
    this.heatScale = function(f) {
        var val = heatValue(f.get("cube"));
        //val = ((val*val) / (max*max));
        //val = val / max;
        val = Math.log2(val+1)/Math.log2(max);
        return val;
    }

    var aggregate = function(o){
        var data = filteredCube[o.getId()]
        return {
            "pickupCount": data.pick.count,
            "dropoffCount": data.drop.count
        };
    };

    var streetLayer = new cube.StreetLayer();
    var heatLayer = new cube.HeatMapLayer(this.heatScale, {
        threshold_min: 0.20,
        threshold_max: 1.00,
    });

    context.dataObj.args.streetLayer = streetLayer.layer;
    var dataObj = new data.Cube(context.dataObj.args);

    var filteredCube = {};

    function LinkCubeFilterForm(onApply) {
        //TODO: Add the road type to the filter form (i.e. primary, secondary, etc.)
        cube.CubeFilterForm.call(this, onApply);

        var heattype = document.createElement('fieldset');
        var legend = document.createElement("legend");
        legend.innerHTML = "Heatmap Type";
        heattype.appendChild(legend);
        this.heattype_pickup = document.createElement("input");
        this.heattype_pickup.type = "radio";
        this.heattype_pickup.name = "heat_type";
        this.heattype_pickup.checked = true;
        var label = document.createElement("label");
        label.innerHTML = "Pickup: ";
        heattype.appendChild(label);
        heattype.appendChild(this.heattype_pickup);
        this.heattype_dropoff = document.createElement("input");
        this.heattype_dropoff.type = "radio";
        this.heattype_dropoff.name = "heat_type";
        var label = document.createElement("label");
        label.innerHTML = "Dropoff: ";
        heattype.appendChild(label);
        heattype.appendChild(this.heattype_dropoff);
        this.heat_inverted = document.createElement("input");
        this.heat_inverted.type = "checkbox";
        this.heat_inverted.label = "Invert: ";

        [heattype, this.heat_inverted].forEach(this.addControl, this);
    }
    LinkCubeFilterForm.prototype = Object.create(cube.CubeFilterForm.prototype);
    LinkCubeFilterForm.prototype.constructor = LinkCubeFilterForm;

    LinkCubeFilterForm.prototype.extendedFields = function LinkCubeFilterFormExtendedFields(fields) {
        fields.pickup = this.heattype_pickup.checked;
        fields.dropoff = this.heattype_dropoff.checked;
        fields.invert = this.heat_inverted.checked;
        return fields;
    }


    function collectionBuilder(self, d) {
        for( let osm in d ) {
            d[osm].drop.details.forEach(function(t, i){
                t.time_inc = util.parseDateTime(t.time_inc);
            });
            d[osm].pick.details.forEach(function(t, i){
                t.time_inc = util.parseDateTime(t.time_inc);
            });
        }
    }

    var delete_me_counter = 0;
    var filter = new LinkCubeFilterForm(function LinkCubeFilterFormApply(formData) {
        // Reset all filters and regenerate them.
        filters = [];

        if( formData.pickup ) {
            heatValue = pickupCountFunction;
        }
        else if( formData.dropoff ) {
            heatValue = dropoffCountFunction;
        }
        if( formData.invert ) {
            heatLayer.threshold_max = 0.99;
            heatLayer.threshold_min = 0.60;
        } else {
            heatLayer.threshold_max = 1.00;
            heatLayer.threshold_min = 0.60;
        }
        heatLayer.invert = formData.invert;

        if( formData.startdate ) {
            filters.push(new cube.DateFilter(formData.startdate, formData.enddate));
        }
        if( formData.starttime ) {
            filters.push(new cube.TimeFilter(formData.starttime, formData.endtime));
        }

        // Filter and update
        filteredCube = {};
        for( let osm in dataObj.cube ) {
            var c = dataObj.cube[osm];
            if( !formData.roadtypes[c.geo.properties.highway].checked ) {
                continue;
            }
            var newOsm = {
                pick: {
                    count: 0,
                    details: []
                },
                drop: {
                    count: 0,
                    details: []
                }
            }
            var newOsm = {};
            var filteredDetails = [];
            var filteredCount = 0;
            function filterAggregate(cell) {
                var i, ii = filters.length;
                if( cell.time_inc === null ) {
                    return;
                }
                for( let i = 0; i < ii; i++ ) {
                    if( filters[i].filter(cell) ) {
                        return;
                    }
                }
                filteredDetails.push(cell);
                filteredCount += cell.count;
            }

            filteredDetails = [];
            filteredCount = 0;
            c.pick.details.forEach(filterAggregate);
            newOsm.pick = {
                count: filteredCount,
                details: filteredDetails,
            }

            filteredDetails = [];
            filteredCount = 0;
            c.drop.details.forEach(filterAggregate);
            newOsm.drop = {
                count: filteredCount,
                details: filteredDetails,
            }
            filteredCube[osm] = newOsm;
        }

        // Create the heatmap layer
        // TODO: Creating heatFeatures is duplicated between link and item cubes.
        var heatFeatures = [];
        max = 0;
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
        console.log("Message ", delete_me_counter, ": New max count =", max);
        heatLayer.regenerate(heatFeatures, 2501);
    });
    dataObj.on("complete", function() {
        filter.apply();
    });

    return {
        "info": {
            "header": ["Name", "Pickup Count", "Dropoff Count"],
            "format": function(o){
                var props = o.getProperties();
                var label = ""
                if( props.name ) {
                    label = props.name;
                } else {
                    label = props.highway + "(" + o.getId() + ")";
                }
                var agg = aggregate(o);
                return [label, agg.pickupCount, agg.dropoffCount];
            },
        },
        "filterForm": filter,
        "layers": [
            streetLayer.layer,
            heatLayer.layer,
        ],
        "getDataObj": function() {
            return dataObj;
        },
        collectionBuilder: collectionBuilder,
        mapUpdate: function(map) {
        }
    };
});