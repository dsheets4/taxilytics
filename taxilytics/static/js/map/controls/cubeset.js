define(['ol', 'js/map/controls/flyout-menu'], function(ol, FlyoutMenu) {

    var CubeSetControl = function(opt_options){
        var opts = {
            "className": "cubelet-menu",
            "tipLabel": "Select one or more cube sets to draw or create new ones"
        }
        for( let prop in opt_options ) {
            opts[prop] = opt_options[prop];
        }
        FlyoutMenu.call(this, 'Cube Sets', opts);
    }
    ol.inherits(CubeSetControl, FlyoutMenu);

    return CubeSetControl;
});
