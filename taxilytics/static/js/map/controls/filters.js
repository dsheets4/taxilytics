define(['ol', 'js/map/controls/flyout-menu'], function(ol, FlyoutMenu) {

    var FilterControl = function(opt_options){
        var opts = {
            "className": "filter-menu",
            "tipLabel": "Set query filters"
        }
        for( let prop in opt_options ) {
            opts[prop] = opt_options[prop];
        }
        FlyoutMenu.call(this, 'Filters', opts);
    }
    ol.inherits(FilterControl, FlyoutMenu);

    return FilterControl;
});
