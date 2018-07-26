define(["ol", "js/map/controls/flyout-menu"], function(ol, FlyoutMenu) {

    // Adapted from: https://github.com/walkermatt/ol3-layerswitcher
    /**
     * OpenLayers 3 Layer Switcher Control.
     * See [the examples](./examples) for usage.
     * @constructor
     * @extends {ol.control.Control}
     * @param {Object} opt_options Control options, extends olx.control.ControlOptions adding:
     *                              **`tipLabel`** `String` - the button tooltip.
     */
    LayerSwitcher = function(opt_options) {
        FlyoutMenu.call(this, "Layers", {
            "className": "layer-switcher",
            tipLabel: "Layer visibility settings"
        });
        this.menu.className += " form-box";
        this.mapListeners = [];
    };
    ol.inherits(LayerSwitcher, FlyoutMenu);

    /**
     * Re-draw the layer panel to represent the current state of the layers.
     */
    LayerSwitcher.prototype.renderMenu = function() {

        this.ensureTopVisibleBaseLayerShown_();

        while(this.menu.firstChild) {
            this.menu.removeChild(this.menu.firstChild);
        }

        var ul = document.createElement("ul");
        ul.className = "layer-form";
        this.menu.appendChild(ul);
        this.renderLayers_(this.getMap(), ul);
    };

    /**
     * Set the map instance the control is associated with.
     * @param {ol.Map} map The map instance.
     */
    LayerSwitcher.prototype.setMap = function(map) {
        // Clean up listeners associated with the previous map
        for (var i = 0, key; i < this.mapListeners.length; i++) {
            this.getMap().unByKey(this.mapListeners[i]);
        }
        this.mapListeners.length = 0;
        // Wire up listeners etc. and store reference to new map
        ol.control.Control.prototype.setMap.call(this, map);
        if (map) {
            var this_ = this;
            // this.mapListeners.push(map.on("pointerdown", function() {
            //     this_.hideMenu();
            // }));
            this.renderMenu();
        }
    };

    /**
     * Ensure only the top-most base layer is visible if more than one is visible.
     * @private
     */
    LayerSwitcher.prototype.ensureTopVisibleBaseLayerShown_ = function() {
        var lastVisibleBaseLyr;
        LayerSwitcher.forEachRecursive(this.getMap(), function(l, idx, a) {
            if ((l.get("type") === "base" || l instanceof ol.layer.Tile) && l.getVisible()) {
                lastVisibleBaseLyr = l;
            }
        });
        if (lastVisibleBaseLyr) this.setVisible_(lastVisibleBaseLyr, true);
    };

    /**
     * Toggle the visible state of a layer.
     * Takes care of hiding other layers in the same exclusive group if the layer
     * is toggle to visible.
     * @private
     * @param {ol.layer.Base} The layer whose visibility will be toggled.
     */
    LayerSwitcher.prototype.setVisible_ = function(lyr, visible) {
        var map = this.getMap();
        lyr.setVisible(visible);
        if (visible && (lyr.get("type") === "base" || lyr instanceof ol.layer.Tile)) {
            // Hide all other base layers regardless of grouping
            LayerSwitcher.forEachRecursive(map, function(l, idx, a) {
                if (l != lyr && (lyr.get("type") === "base" || l instanceof ol.layer.Tile)) {
                    l.setVisible(false);
                }
            });
        }
    };

    /**
     * Render all layers that are children of a group.
     * @private
     * @param {ol.layer.Base} lyr Layer to be rendered (should have a title property).
     * @param {Number} idx Position in parent group list.
     */
    LayerSwitcher.prototype.renderLayer_ = function(lyr, idx) {

        var this_ = this;

        var li = document.createElement("li");

        var lyrTitle = lyr.get("title");
        var lyrId = LayerSwitcher.uuid();

        var layerCtrls = document.createElement("div");
        layerCtrls.className = "form-box";
        li.appendChild(layerCtrls);

        if (lyr.getLayers && !lyr.get("combine")) {

            li.className = "group";
            var label = document.createElement("label");
            label.innerHTML = lyrTitle;
            layerCtrls.appendChild(label);
            var ul = document.createElement("ul");
            layerCtrls.appendChild(ul);

            this.renderLayers_(lyr, ul);

        } else {
            li.className = "layer";
            var input = document.createElement("input");
            if (lyr.get("type") === "base" || lyr instanceof ol.layer.Tile) {
                input.type = "radio";
                input.name = "base";
            } else {
                input.type = "checkbox";
            }
            input.id = lyrId;
            input.checked = lyr.get("visible");
            input.onchange = function(e) {
                this_.setVisible_(lyr, e.target.checked);
            };
            layerCtrls.appendChild(input);

            var label = document.createElement("label");
            label.htmlFor = lyrId;
            label.innerHTML = lyrTitle;
            layerCtrls.appendChild(label);

            var vis = document.createElement("input");
            vis.htmlFor = lyrId;
            vis.type = "range";
            vis.className = "opacity";
            vis.min = 0;
            vis.max = 1;
            vis.step = 0.1;
            vis.onchange = function() {
                lyr.setOpacity(parseFloat(this.value));
            };
            vis.value = lyr.getOpacity();
            vis.oninput = vis.onchange;
            layerCtrls.appendChild(vis);
        }

        return li;

    };

    /**
     * Render all layers that are children of a group.
     * @private
     * @param {ol.layer.Group} lyr Group layer whos children will be rendered.
     * @param {Element} elm DOM element that children will be appended to.
     */
    LayerSwitcher.prototype.renderLayers_ = function(lyr, elm) {
        var lyrs = lyr.getLayers().getArray().slice().reverse();
        for (var i = 0, l; i < lyrs.length; i++) {
            l = lyrs[i];
            if (l.get("title")) {
                elm.appendChild(this.renderLayer_(l, i));
            }
        }
    };

    /**
     * **Static** Call the supplied function for each layer in the passed layer group
     * recursing nested groups.
     * @param {ol.layer.Group} lyr The layer group to start iterating from.
     * @param {Function} fn Callback which will be called for each `ol.layer.Base`
     * found under `lyr`. The signature for `fn` is the same as `ol.Collection#forEach`
     */
    LayerSwitcher.forEachRecursive = function(lyr, fn) {
        lyr.getLayers().forEach(function(lyr, idx, a) {
            fn(lyr, idx, a);
            if (lyr.getLayers) {
                LayerSwitcher.forEachRecursive(lyr, fn);
            }
        });
    };

    /**
     * Generate a UUID
     * @returns {String} UUID
     *
     * Adapted from http://stackoverflow.com/a/2117523/526860
     */
    LayerSwitcher.uuid = function() {
        return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function(c) {
            var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
            return v.toString(16);
        });
    }

    return LayerSwitcher;
});
