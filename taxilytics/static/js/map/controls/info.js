define(['ol', 'js/map/controls/flyout-menu'], function(ol, FlyoutMenu) {

    var InfoControl = function(opt_options){
        var opts = {
            "className": "info-menu",
            "tipLabel": "View selection info"
        }
        for( prop in opt_options ) {
            opts[prop] = opt_options[prop];
        }
        FlyoutMenu.call(this, 'Info', opts);
    }
    ol.inherits(InfoControl, FlyoutMenu);

    return InfoControl;
});
