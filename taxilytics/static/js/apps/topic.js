define([],
function() {
    return {
        "info": function(o){
            var props = o.getProperties();
            return o.getId() + ": " + props.level;
        }
    };
});