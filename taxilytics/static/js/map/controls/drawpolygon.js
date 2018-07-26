define(['ol'], function(ol) {

    var drawPoly = {};

    drawPoly.Control = function(map, drawLayer, opt_options) {

	    var myUrl = window.location.href;
	    if( myUrl.includes('?') ) {
	        myUrl += "&";
	    } else {
	        myUrl += "?";
	    }

        var options = opt_options || {};
        options.queryOp = options.queryOp || 'contained';
        var dataLayer = options.dataLayer;
        options.drawend = options.drawend || function(drawnFeature){
            var geom = new ol.format.WKT().writeFeature(drawnFeature);
            map.setData({
                next: myUrl + "geo=" + geom + "&op=" + options.queryOp
            }, dataLayer);
        }

        var button = document.createElement('button');
        button.innerHTML = options.label || 'Draw';

        var this_ = this;
        var draw;
        var startDraw = function(type) {
            if (draw != null) {
                cancelDraw();
            }

            draw = new ol.interaction.Draw({
                source: drawLayer.getSource(),
                type: 'Polygon'
            });
            draw.on('drawend', function(e) {
                cancelDraw();
                var geom = new ol.format.WKT().writeFeature(e.feature);
                if( options.drawend ){
                    options.drawend(e.feature);
                }
            });
            map.addInteraction(draw);
        }
        var cancelDraw = function() {
            if(draw == null)return;

            map.removeInteraction(draw);
        }

        button.addEventListener('click', startDraw, false);
        button.title = 'Draw a geospatial query region';
        //button.className = "draw-poly";
        button.appendChild(document.createElement('div'));

        var element = document.createElement('div');
        element.className = 'draw-poly ol-unselectable ol-control';
        element.appendChild(button);

        ol.control.Control.call(this, {
            element: element,
            target: options.target,
        });

	    map.addControl(this);

        return this;
    };
    ol.inherits(drawPoly.Control, ol.control.Control);

    return drawPoly;
});