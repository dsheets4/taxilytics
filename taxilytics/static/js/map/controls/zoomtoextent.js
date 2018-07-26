define(['ol'], function(ol) {
    return {
        ExtentZoom: function(extent) {
            zoom = new ol.control.ZoomToExtent({
                label: "E",
                extent: extent,
                tipLabel: "Zoom to data extent"
            })
            return zoom;
        }
    }
});