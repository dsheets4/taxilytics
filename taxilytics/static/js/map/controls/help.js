define(['ol', 'js/map/controls/flyout-menu'], function(ol, FlyoutMenu) {

    var HelpFlyoutMenu = function(opt_options){
        var opts = {
            "className": "help-menu",
            "tipLabel": "Application Controls"
        }
        for( let prop in opt_options ) {
            opts[prop] = opt_options[prop];
        }
        FlyoutMenu.call(this, 'Help', opts);
    }
    ol.inherits(HelpFlyoutMenu, FlyoutMenu);

    return HelpFlyoutMenu;
});
