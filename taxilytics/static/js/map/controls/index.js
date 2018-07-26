define(
    [
        'ol',
        'js/map/controls/drawpolygon',
        'js/map/controls/mouse',
        'js/map/controls/selection',
        'js/map/controls/zoomtoextent',
        'js/map/controls/overview',
        'js/map/controls/layers',
        'js/map/controls/filters',
        'js/map/controls/info',
        'js/map/controls/help',
        'js/map/controls/loading',
        'js/map/controls/cubeset'
    ],
    function(
            ol, drawPoly, mouse, selection, zoomtoextent, overview,
            layers, filters, info, help,
            load, cubeset) {
        return {
            Selector: selection.Selector,
            ExtentZoom: zoomtoextent.ExtentZoom,
            OverviewMap: overview,
            posToLatLon: mouse.posToLatLon,
            drawPoly: drawPoly,
            Layers: layers,
            Filters: filters,
            Info: info,
            Help: help,
            Loading: load,
            CubeSet: cubeset
        }
    }
);
