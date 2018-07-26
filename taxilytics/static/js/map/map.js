define(["js/3rdparty/ol",
        "js/config",
        "js/map/controls",
        "js/forms",
        "js/map/data",
        "js/apps"],
function(ol, cfg, controls, forms, data, apps) {

    var Map = function(dataObj, context, target_elem) {
        target_elem = target_elem || "content";
        initial_data = initial_data || {};

        var home = new cfg.Home("Hangzhou");

        var options = context.mapOptions || {};
        var mapLayers = new ol.layer.Group({
            title: "Base Maps",
            layers: [
                new ol.layer.Tile({
                    title: "Road (OSM)",
                    source: new ol.source.OSM(),
                    visible: true,
                    opacity: 0.4,
                }),
            ]
        });

        this.overlays = new ol.layer.Group({
            title: "Overlays"
        });

	    this.traj_layers = new ol.layer.Group({
	        title: "Trajectories"
	    });

	    var loadControl = new controls.Loading({
            cancelFunction: function() {
                dataObj.cancelOperation();
            }
        });
        dataObj.on("start", loadControl.startLoad, loadControl);
        dataObj.on("complete", loadControl.endLoad, loadControl);

        ol.Map.call(this, {
            layers: [mapLayers, this.overlays, this.traj_layers],
            // TODO: Recreate the renderer that reduced the size of lines on zoom.
            // renderer: exampleNS.getRendererFromQueryString(),
            target: target_elem,
            view: new ol.View({
                center: home.centerPt,
                zoom: 18
            }),
            controls: ol.control.defaults({
                 attributionOptions: { collapsible: true }
              }).extend([
                 new ol.control.ScaleLine(),
                 new ol.control.FullScreen(),
                 new ol.control.MousePosition({
                     coordinateFormat: controls.posToLatLon
                 }),
                 new ol.control.ZoomSlider(),
                 new controls.OverviewMap(),
                 new controls.Layers(),
                 loadControl
              ]),
            interactions: ol.interaction.defaults().extend([
                  new ol.interaction.DragZoom(),
                  ]),
        });
        var self = this;

        context.app.getMapControls().forEach(function(c){
            this.addControl(c);
        }, this);
        var filterForm, infoForm;
        if( context.app.filterForm && context.app.filterForm.form) {
            filterForm = new forms.Filter(context.app.filterForm.form);
            this.addControl(new controls.Filters({form: filterForm.form}));
            context.app.filterForm.map = this;
        }
        if( context.app.info ) {
            console.log("Info object: ", context.app.info);
            infoForm = new forms.Info(context.app.info);
            this.addControl(new controls.Info({form: infoForm.form}));
        }
        var helpForm = new forms.Help(context.app.help);
        this.addControl(new controls.Help({form: helpForm.form}));

        if( typeof(context.app.onMapUpdate) !== "undefined" ) {
            self.getView().on("propertychange", function(e) {
                context.app.onMapUpdate(e, self);
            });
        }

        var color_id = -1;
        var selectableLayers = [this.traj_layers];
        if( context.app.layers ) {
            context.app.layers.forEach(function addSelectableLayers(l) {
                if( l instanceof ol.layer.Group ) {
                    self.getLayers().push(l);
                } else {
                    self.overlays.getLayers().push(l);
                }
                if( l.get('selectable') ) {
                    selectableLayers.push(l);
                }
            })
        }

        this.selector = new controls.Selector(
            this,
            selectableLayers,
            infoForm.selectCallback,
            infoForm.clearCallback
        );

        var extentZoom = new controls.ExtentZoom();
        this.addControl(extentZoom);

        this.getExtents = function (objs) {
            if(typeof(objs) === "undefined") { objs = [self.traj_layers] }
            var extent = ol.extent.createEmpty();
            objs.forEach(function (obj) {
                if( obj instanceof ol.layer.Group ) {
                    if( obj.getVisible() ) {
                        extent = ol.extent.extend(extent, self.getExtents(obj.getLayers()));
                    }
                }
                else if( obj instanceof ol.layer.Layer ) {
                    if( obj.getVisible() ) {
                        extent = ol.extent.extend(extent, obj.getSource().getExtent());
                    }
                }
                else { console.log("Unmatched extent type: ", obj) }
            });
            if( ol.extent.isEmpty(extent) ) {
                return home.extent;
            }
            return extent;
        }

        this.zoomToFitData = function () {
            self.getView().fit(
                self.getExtents([self.traj_layers]),
                self.getSize()
            );
        }

        this.layerCounter = 0;

        this.addGeoJson = function (d, layer) {
            console.log(new Date(), "Input GeoJSON: ", d);
            if( d.type == "FeatureCollection" && d.features.length == 0 ) {
                self.zoomToFitData();
                return;
            }
            if( d.type == "Feature" ) {
                // Transform Feature to FeatureCollection
                d = {
                    crs: {
                        type: "name",
                        properties: {
                            name: "EPSG:3857"
                        }
                    },
                    features: [d],
                    type: "FeatureCollection"
                }
            }
            var features = (new ol.format.GeoJSON())
              .readFeatures(d, {featureProjection: 'EPSG:3857'});

            if( 'id' in d )
                color_id = d.id;
            else {
                color_id = self.layerCounter;
                self.layerCounter++;
            }

            if( !layer ) {
                layer = new ol.layer.Vector({
                    title: 'Query Data Layer ' + self.layerCounter,
                    source: new ol.source.Vector(),
                    style: (function() {
                        style_cache = {};
                        var defaultStyle = new ol.style.Style({
                            stroke: new ol.style.Stroke({
                                color: cfg.colorTbl.GetColorStringRgba(color_id, 0.8),
                                width: 3
                            }),
                            fill: new ol.style.Fill({
                                color: cfg.colorTbl.GetColorStringRgba(color_id, 0.4),
                            }),
                            image: new ol.style.Circle({
                                radius: 10,
                                fill: null,
                                stroke: new ol.style.Stroke({
                                    color: cfg.colorTbl.GetColorStringRgba(color_id, 0.8),
                                })
                            })
                        });
                        return function(feature, resolution) {
                            style = defaultStyle;
                            return [style];
                        }
                    })()
                });
                self.traj_layers.getLayers().push(layer);
            }
            layer.getSource().addFeatures(features);

            self.zoomToFitData();

            // This seems inefficient, is there a way to just set the extents
            // of the existing control?  Not currently...
            // http://openlayers.org/en/latest/apidoc/ol.control.ZoomToExtent.html
            self.removeControl(extentZoom);
            extentZoom = new controls.ExtentZoom(self.getExtents())
            self.addControl(extentZoom);
        };

        this.dataObj = dataObj;
        this.dataObj.on("data", this.addGeoJson, this);

        this.setData = function(d, layer) {
            self.dataObj.setData(d, layer);
        };

        this.drawLayer = new ol.layer.Vector({
            title: 'Query Regions',
            source : new ol.source.Vector(),
            style : new ol.style.Style({
                fill : new ol.style.Fill({
                    color : 'rgba(255, 255, 255, 0.2)'
                }),
                stroke : new ol.style.Stroke({
                    color : '#ffcc33',
                    width : 4
                }),
                image : new ol.style.Circle({
                    radius : 5,
                    fill : new ol.style.Fill({
                        color : '#ffcc33'
                    })
                })
            })
        });
        this.overlays.getLayers().push(this.drawLayer);

        if( context.app.draw ) {
            var drawPolygonControl = new controls.drawPoly.Control(this, this.drawLayer, context.app.draw);
        }

        // Attempt to change cursor when over selectable features but it changes when close
        // instead of only when directly over (i.e. clicking would select the feature).
        //self.on('pointermove', function(e) {
        //    if (e.dragging) { return; }
        //    var hit = self.hasFeatureAtPixel(e.pixel);
        //    self.getTargetElement().style.cursor = hit ? 'pointer' : '';
        //});

        this.zoomToFitData();
    }
    ol.inherits(Map, ol.Map);

    return {
        Map: Map
    }
});
