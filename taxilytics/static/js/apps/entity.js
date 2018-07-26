define([],
function() {
    return {
        "info": {
            "header": [],
            "format": function(o){
                var props = o.getProperties();
                return props.common_id + ": " + props.start_datetime;
            }
        }
    }
});