define([
    "ol",
],
function(ol) {

    function HeatMapLayer(heatValue, opt_options) {
        var self = this;
        opt_options = opt_options || {};

        // Create the heatmap layer and setup defaults
        var opacity = opt_options.opacity || 1.0;//0.15;
        this.invert = opt_options.invert || false;
        this.heatValue = heatValue;
        this.source = new ol.source.Vector();
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

        this.max = -Infinity;
        this.min = Infinity;

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

    HeatMapLayer.prototype.clear = function clear() {
        this.heatLayer.getSource().clear();
        this.streetLayer.getSource().clear();
        this.source.clear();
    }

    var timer_counter = 0;
    HeatMapLayer.prototype.setSource = function setSource(newSource) {
        var self = this;
        //var timer = new util.Timer("item_cube.processHeatFeatures");

        var heatFeatures = [];
        this.max = -Infinity;
        this.min = Infinity;
        this.heatLayer.getSource().clear();
        this.streetLayer.getSource().clear();
        newSource.forEachFeature(function(f) {
            var h = self.heatValue(f);
            if( h == 0 ) {
                return;
            }
            this.max = Math.max(this.max, isNaN(h) ? -Infinity : h);
            this.min = Math.min(this.min, isNaN(h) ?  Infinity : h);
            var clone = f.clone();
            clone.set("heat", h);
            self.source.addFeature(clone);
        });
        //timer.stop();
        //if( typeof(benchmarks) !== "undefined" ) {
        //    console.log("Message ", ++timer_counter,
        //        ": Total streets =", heatFeatures.length,
        //        ": New max count =", this.max
        //    );
        //}
        return heatFeatures;
    }

    HeatMapLayer.prototype.regenerate = function regenerate(zoomLevel) {
        //var timer = new util.Timer("HeatMapLayer.regenerate");
        var ptSpacing = 150;  // Higher numbers generate fewer points.
        if( typeof(zoomLevel) !== "undefined" ) {
            if(zoomLevel > 500){ ptSpacing = 500; }
            if(zoomLevel < 1){ ptSpacing = zoomLevel*5; }
            else{ ptSpacing = zoomLevel*10; }
        }
        this.heatLayer.getSource().clear();
        this.streetLayer.getSource().clear();
        this.source.forEachFeature(function streetToHeat(f) {
            f = f.clone();
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
        //var end_time = new Date();
        //timer.stop(true);
    }

    return HeatMapLayer;
});