define(["js/3rdparty/ol", "js/config", "js/map/data", "js/util", "js/ui"],
function(ol, cfg, data, util, ui) {

    function CubeFilterForm(onApply) {
        var self = this;
        this.addControl = function(ctrl) {
            var div = document.createElement('div');
            if( ctrl.label ) {
                var label = document.createElement('label');
                label.innerHTML = ctrl.label;
                div.appendChild(label);
            }
            div.className = "form-box";
            div.appendChild(ctrl);
            self.form.insertBefore(div, this.applyButton);
        }

        this.onApply = onApply;
        this.form = document.createElement('div');
        this.form.className = "filter-form";

        var roads = [
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
            //'turning_circle'
        ]
        var roadtype = document.createElement('fieldset');
        var legend = document.createElement("legend");
        legend.innerHTML = "Road Types";
        roadtype.appendChild(legend);
        this.roadtypes = {};
        roads.forEach(function(r, i){
            var cb = document.createElement("input");
            cb.type = "checkbox";
            cb.name = "roadtype";
            cb.value = r;
            cb.checked = true;
            roadtype.appendChild(cb);
            var label = r.charAt(0).toUpperCase() + r.slice(1).replace('_', ' ');
            roadtype.appendChild(document.createTextNode(label + " "));
            this.roadtypes[r] = cb;
            if( i > 0 && (i%5) == 0 ) {
                roadtype.appendChild(document.createElement("br"));
            }
        }, this);
        roadtype.appendChild(document.createElement("br"));
        var checkAllButton = document.createElement("input");
        checkAllButton.type = "button";
        checkAllButton.name = "checkall";
        checkAllButton.value = "Check All";
        checkAllButton.onclick = function(e) {
            for( let r in self.roadtypes ) {
                self.roadtypes[r].checked = true;
            };
        };
        roadtype.appendChild(checkAllButton);
        var uncheckAllButton = document.createElement("input");
        uncheckAllButton.type = "button";
        uncheckAllButton.name = "checkall";
        uncheckAllButton.value = "Uncheck All";
        uncheckAllButton.onclick = function(e) {
            for( let r in self.roadtypes ) {
                self.roadtypes[r].checked = false;
            };
        };
        roadtype.appendChild(uncheckAllButton);

        this.applyButton = document.createElement('button');
        this.applyButton.innerHTML = "Apply";
        this.applyButton.addEventListener("click", function() {
            self.apply();
        });


        var fs = document.createElement("fieldset");
        var legend = document.createElement("legend");
        legend.innerHTML = "Time";
        fs.appendChild(legend);
        this.timeRange = new ui.DateTimeRangeSlider(fs);
        this.form.appendChild(this.applyButton);

        [fs, roadtype].forEach(this.addControl, this);
    }

    CubeFilterForm.prototype.apply = function() {
        // Reset all filters and regenerate them.
        var startdate = "";
        var enddate = "";
        var starttime = "";
        var endtime = "";

        var timeExtents = this.timeRange.selected();
        startdate = timeExtents[0];
        enddate = timeExtents[1];

        var fields = this.extendedFields({
            startdate: startdate,
            enddate: enddate,
            starttime: starttime,
            endtime: endtime,
            roadtypes: this.roadtypes,
            timeMode: "DateTime",
        });
        this.onApply(fields);
    }


    // Returns true if the value does not pass the filter.
    function DateFilter(start, end) {
        // Clamp the input to just the dates.
        this.start = new Date(start.getUTCFullYear(), start.getUTCMonth(), start.getUTCMonth());
        this.end = new Date(end.getUTCFullYear(), end.getUTCMonth(), end.getUTCMonth());
        this.filter = function(t) {
            return t < this.start || t > this.end;
        }
    }


    // Returns true if the value does not pass the filter.
    function TimeFilter(start, end) {

        function extractSecondsOfDay(t) {
            return t.getHours()*60*60 + t.getMinutes()*60 + t.getSeconds();
        }
        this.start = extractSecondsOfDay(start);
        this.end = extractSecondsOfDay(end);
        this.filter = function(t) {
            var tod = extractSecondsOfDay(t);
            return tod < this.start || tod > this.end;
        }
    }


    // Returns true if the value does not pass the filter.
    function DateTimeFilter(start, end) {
        this.start = start;
        this.end = end;
        this.filter = function(t) {
            return t < this.start || t > this.end;
        }
    }


    function RegionCubeSetLayer(opt_options) {
        opt_options = opt_options || {};

        // Create the region layer and setup defaults
        var colorId = opt_options.colorId || -1;
        var opacity = opt_options.opacity || 0;
        var title = opt_options.title || "Region Cube Sets";
        this.layer = new ol.layer.Vector(
        {
            title: title,
            selectable: false,
            source: new ol.source.Vector(),
        });
        this.layer.setOpacity(opacity);
    }


    function StreetLayer(opt_options) {
        opt_options = opt_options || {};

        // Create the street layer and setup defaults
        var streetColorId = opt_options.streetColorId || -1;
        var streetOpacity = opt_options.streetOpacity || 0;
        this.layer = new ol.layer.Vector({
            title: 'Streets',
            selectable: true,
            source: new ol.source.Vector(),
            style: (function() {
                var defaultStyle = new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: cfg.colorTbl.GetColorStringRgba(streetColorId, 0.8),
                        width: 5
                    }),
                    fill: new ol.style.Fill({
                        color: cfg.colorTbl.GetColorStringRgba(streetColorId, 0.4),
                    }),
                    image: new ol.style.Circle({
                        radius: 10,
                        fill: null,
                        stroke: new ol.style.Stroke({
                            color: cfg.colorTbl.GetColorStringRgba(streetColorId, 0.8),
                        })
                    })
                });
                return function(feature, resolution) {
                    style = defaultStyle;
                    return [style];
                }
            })()
        });
        this.layer.setOpacity(streetOpacity);
    }


    function HeatMapLayer(heatValue, opt_options) {
        var self = this;
        opt_options = opt_options || {};

        // Create the heatmap layer and setup defaults
        var opacity = opt_options.opacity || 1.0;//0.15;
        this.invert = opt_options.invert || false;
        this.heatValue = heatValue;
        this.threshold_min = opt_options.threshold_min || 0.20;
        this.threshold_max = opt_options.threshold_max || 1.0;
        this.heatWeight = function(f) {
            var val = self.heatValue(f);
            if( self.invert ) {
                val = 1 - val;
            }
            if( val < this.threshold_min ) {
                val = 0.0;
            }
            else if ( val > this.threshold_max ) {
                val = 1.0;
            }
            else{
                val = (val - this.threshold_min) / (this.threshold_max - this.threshold_min);
            }
            return val;
        }

        this.heatLayer = new ol.layer.Heatmap({
            title: "Heat Overlay",
            source: new ol.source.Vector(),
            weight: this.heatWeight,
            maxResolution: 500  // Max zoom level at which the heatmap is rendered
        });
        this.heatLayer.setOpacity(opacity);
        this.streetLayer = new ol.layer.Vector({
            title: "Low value streets",
            source: new ol.source.Vector(),
            style: (function() {
                var defaultStyle = new ol.style.Style({
                    stroke: new ol.style.Stroke({
                        color: "#00FF00",
                        width: 3
                    }),
                    fill: new ol.style.Fill({
                        color: "#00FF00",
                    }),
                    image: new ol.style.Circle({
                        radius: 10,
                        fill: null,
                        stroke: new ol.style.Stroke({
                            color: "#00FF00",
                        })
                    })
                });
                return function(feature, resolution) {
                    style = defaultStyle;
                    return [style];
                }
            })()
        });
        this.streetLayer.setOpacity(0.3);//opacity);
        this.layer = new ol.layer.Group({
            title: "Street Heat Map",
            layers: [this.streetLayer, this.heatLayer]
        });

        this.sphere = new ol.Sphere(ol.proj.EPSG3857.RADIUS);
    }

    HeatMapLayer.prototype.regenerate = function(features, zoomLevel) {
        var timer = new util.Timer("HeatMapLayer.regenerate");
        var ptSpacing = 150;  // Higher numbers generate fewer points.
        if( typeof(zoomLevel) !== "undefined" ) {
            if(zoomLevel > 500){ ptSpacing = 500; }
            if(zoomLevel < 1){ ptSpacing = zoomLevel*5; }
            else{ ptSpacing = zoomLevel*10; }
        }
        this.heatLayer.getSource().clear();
        this.streetLayer.getSource().clear();
        features.forEach(function streetToHeat(f) {
            var value = this.heatWeight(f);
            if( value < this.threshold_min || value > this.threshold_max  ) {
                this.streetLayer.getSource().addFeature(f);
                return;
            }

            // Rescale the remaining numbers between low and high threshold.

            var coords = f.getGeometry().getCoordinates();
            var newCoords = [];

            // Creates a smoother line for use with the heatmap.
            f.getGeometry().forEachSegment(function(p1, p2) {
                //newCoords.push(p1);
                var dist = this.sphere.haversineDistance(
                    ol.proj.transform(p1, 'EPSG:3857', 'EPSG:4326'),
                    ol.proj.transform(p2, 'EPSG:3857', 'EPSG:4326'));
                var segments = dist / ptSpacing;
                var i;
                for( let i=1; i<segments; i++ ) {
                    var dt = i/segments;
                    newCoords.push([
                        p1[0] + ( dt * (p2[0] - p1[0]) ),
                        p1[1] + ( dt * (p2[1] - p1[1]) )
                    ]);
                }
            }, this);
            if( newCoords.length == 0 ) {
                var coords = f.getGeometry().getCoordinates();
                newCoords.push(coords[Math.floor(coords.length/2)]);
            }
            f.setGeometry(new ol.geom.MultiPoint(newCoords));
            this.heatLayer.getSource().addFeature(f);
        }, this);
        var end_time = new Date();
        timer.stop(true);
    }

    return {
        "CubeFilterForm": CubeFilterForm,
        "TimeFilter": TimeFilter,
        "DateFilter": DateFilter,
        "DateTimeFilter": DateTimeFilter,
        "StreetLayer": StreetLayer,
        "HeatMapLayer": HeatMapLayer,
        "RegionCubeSetLayer": RegionCubeSetLayer,
    }
});