define([
    "js/util"
],
function(util) {
    var util = {};

    var defaultOpts = {};
    util.binarySearch = function binarySearch(list, item, comparator, opts) {
        opts = opts || defaultOpts;
        var min = opts.min || 0;
        var max = opts.max || list.length - 1;
        var approx = opts.approx || "";
        var currIdx;
        var cmp;

        while (min <= max) {
            currIdx = Math.floor((min + max) / 2);

            var cmp = comparator(list[currIdx], item);
            if( cmp == 0 ) {
                return currIdx;
            }
            else {
                if( cmp > 0 ) {
                    max = currIdx - 1;
                }
                else {
                    min = currIdx + 1;
                }
            }
        }

        if( typeof(approx) !== "undefined" && typeof(currIdx) !== "undefined" ) {
            var cmp = comparator(list[currIdx], item);
            switch(approx) {
                case "upper":
                    while( cmp < 0 ) {
                        if( currIdx+1 == list.length ) { return null; }
                        cmp = comparator(list[++currIdx], item);
                    }
                    return currIdx;
                case "lower":
                    while( cmp > 0 ) {
                        if( currIdx-1 < 0 ) { return null; }
                        cmp = comparator(list[--currIdx], item);
                    }
                    return currIdx;
            }
        }
        return null;
    }

    util.compare = function compare(a, b) {
        if( a > b ) return 1;
        if( a < b ) return -1;
        return 0;
    }

    return util;
});