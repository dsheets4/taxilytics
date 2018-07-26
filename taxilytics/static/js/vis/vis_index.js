define([
    'js/vis/chart',
    'js/vis/line',
    'js/vis/bar',
    'js/vis/map',
],
function(chart, line, bar, map) {
    return {
        "Chart": chart,
        "LineChart": line,
        "BarChart": bar,
        "Map": map,
    };
});