define([
    'streetcube/js/vis/map',
    'streetcube/js/vis/cubevis-chartjs-canvas',
    'streetcube/js/vis/chartjs-xaxis-brush',
],
function(map, cubevisChartJSCanvas, xAxisBrush) {
    // Simply loading chartjs-xaxis-brush will register the plugin with ChartJS.
    return {
        "CubeVis": cubevisChartJSCanvas,
        "Map": map,
    };
});