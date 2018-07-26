define(["ol"], function(ol) {

    function iterateGroups(objs, f) {
        objs.forEach(function (obj) {
            if( obj.getVisible() ) {
                if( obj instanceof ol.layer.Group ) {
                    iterateGroups(obj.getLayers(), f);
                }
                else if( obj instanceof ol.layer.Layer ) {
                    f(obj);
                }
                else { console.log("Unmatched extent type: ", obj) }
            }
        });
    }

    var ClickSelector = function (layers) {
        var clickLayers = layers;
        ol.interaction.Select.call(this, {
            multi: true,
            layers: clickLayers
        });
    };
    ol.inherits(ClickSelector, ol.interaction.Select);

    var BoxSelector = function (layers) {
        ol.interaction.DragBox.call(this, {
            condition: ol.events.condition.altShiftKeysOnly,
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: [0,50,255,0.75]
                })
            })
        });
    }
    ol.inherits(BoxSelector, ol.interaction.DragBox);

    var Selector = function(map, selectableLayers, selectCallback, clearCallback) {
        var self = this;
        ol.interaction.Select.call(this, {
            multi: true
        });
        var boxSelector = new BoxSelector(selectableLayers);
        var clickSelector = new ClickSelector(selectableLayers);
        this.selectedFeatures = clickSelector.getFeatures();

        if( selectCallback ) {
            this.selectedFeatures.on("add", selectCallback);
        }

        clickSelector.on("select", function(e) {
            self.dispatchEvent("select")
        });

        boxSelector.on("boxend", function(e) {
            var extent = e.target.getGeometry().getExtent();
            function findFeatures(obj) {
                obj.getSource().forEachFeatureIntersectingExtent(extent, function (feature) {
                    self.selectedFeatures.push(feature);
                });
            }
            iterateGroups(selectableLayers, findFeatures);
            self.dispatchEvent("select");
        });

        var clearSelection = function (){
	    	clickSelector.getFeatures().clear();
	    	if(clearCallback) { clearCallback(); }
            self.dispatchEvent("select");
	    }
	    boxSelector.on("boxstart", clearSelection);

	    map.on("click", clearSelection);
        map.addInteraction(boxSelector);
        map.addInteraction(clickSelector);
    }
    ol.inherits(Selector, ol.interaction.Select);

	return {
	    Selector: Selector
    }
});
