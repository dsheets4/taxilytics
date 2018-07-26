define(['ol'], function(ol) {

    var OverviewMapControl = function() {
        ol.control.OverviewMap.call(this, {
            className: 'ol-overviewmap ol-custom-overviewmap',
            layers: [
              new ol.layer.Tile({
                source: new ol.source.OSM({
                  'url': 'http://{a-c}.tile.opencyclemap.org/cycle/{z}/{x}/{y}.png'
                })
              })
            ],
            collapsed: false
        });
    }
    ol.inherits(OverviewMapControl, ol.control.OverviewMap);

    return OverviewMapControl;
});