define(["js/map/data",],
function(data) {
    var dataObj = null;
    var mapControls = [];

    return {
        "info": {
            "format": function(o){
                var props = o.getProperties();
                if( props.name ) {
                    return [props.name];
                } else {
                    return [props.highway + " (" + o.getId() + ")"];
                }
            },
            "header": ["Name"],
        },
        "getDataObj": function() {
            if( !dataObj ) {
                dataObj = new data.Rest();
            }
            return dataObj;
        },
        "getMapControls": function() {
            return mapControls;
        },
        draw: {
            label: "Draw"
        }
    };
});