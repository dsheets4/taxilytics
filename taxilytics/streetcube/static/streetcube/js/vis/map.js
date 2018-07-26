define([
    "ol",
    "js/util",
    "js/map/controls",
],
function(ol, util, controls) {
    var map = {};

    var precision = 6;
    function mousePosToLatLon(coordinate) {
        var lonlat = ol.proj.transform(coordinate, 'EPSG:3857', 'EPSG:4326');
        return "(" + lonlat[1].toFixed(precision) + "," + lonlat[0].toFixed(precision) + ")";
    }

    function Map(targetElem, options) {
        this.options = options;

        var mapLayers = new ol.layer.Group({
            title: "Base Maps",
            layers: [
                new ol.layer.Tile({
                    title: "Road (OSM)",
                    source: new ol.source.OSM(),
                    visible: true,
                    opacity: 0.7,
                }),
            ]
        });

	    this.street_layers = new ol.layer.Group({
	        title: "Region Streets"
	    });

	    this.region_layers = new ol.layer.Group({
	        title: "Region Areas"
	    });

        ol.Map.call(this, {
            layers: [this.street_layers, this.region_layers, mapLayers],
            target: targetElem,
            view: new ol.View({
                center: ol.proj.fromLonLat([120.22600, 30.24050]),
                zoom: 18
            }),
            controls: [
                new ol.control.Zoom(),
                new ol.control.Rotate(),
                new ol.control.Attribution(),
                new ol.control.ScaleLine(),
                new ol.control.FullScreen(),
                new ol.control.MousePosition({
                    coordinateFormat: mousePosToLatLon
                }),
                new ol.control.ZoomSlider(),
                new controls.OverviewMap(),
                new controls.Layers(),
                // loadControl
            ],
            interactions: ol.interaction.defaults().extend([
                new ol.interaction.DragZoom()
            ]),
        });
    }
    ol.inherits(Map, ol.Map);

    this.layerCounter = 0;
    var defaultOpacity = {
        region: 0,
        street: 1,
    };
    Map.prototype.addSource = function(source, type, title) {
        layer = new ol.layer.Vector({
            title: title,
            source: source,
            opacity: defaultOpacity[type]
        });
        this[type+"_layers"].getLayers().push(layer);
    }

    Map.prototype.createFeatureSelector = function(source, handler) {
        var self = this;
	    var dragBox = new ol.interaction.DragBox({
            condition: ol.events.condition.altShiftKeysOnly,
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: [0,50,255,0.75]
                })
            })
        });

        dragBox.on("boxend", function(e) {
            var extent = e.target.getGeometry().getExtent();
            var selectedFeatures = [];
            source.forEachFeatureIntersectingExtent(extent, function(f) {
                selectedFeatures.push(f);
            });
            selectedFeatures = new ol.format.GeoJSON().writeFeaturesObject(selectedFeatures, {
                featureProjection: 'EPSG:3857',
                dataProjection: 'EPSG:4326'
            }).features;
            self.options.onSelection(selectedFeatures);
        });

        this.addInteraction(dragBox);
    }

    Map.prototype.createSourceFromFeatures = function(features) {
        var features = (new ol.format.GeoJSON())
          .readFeatures(features, {
              dataProjection: 'EPSG:3857',
              featureProjection: 'EPSG:3857'
          });
        var source = new ol.source.Vector();
        source.addFeatures(features);
        return source;
    }

    Map.prototype.getViewExtent = function(coordRef) {
        if( typeof(coordRef) === "undefined" ) coordRef = "EPSG:3857"
        var extent = this.getView().calculateExtent(this.getSize());
        extent = ol.proj.transformExtent(extent, "EPSG:3857", coordRef);
        return extent;
    }

    Map.prototype.setViewExtent = function(extent, coordRef) {
        if( typeof(coordRef) === "undefined" ) coordRef = "EPSG:3857"
        extent = ol.proj.transformExtent(extent, coordRef, "EPSG:3857");
        this.getView().fit(extent);
    }

    return Map;
});