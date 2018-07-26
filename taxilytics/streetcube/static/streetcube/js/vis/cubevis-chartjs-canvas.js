define([
    "Chart",
    "js/util",
],
function(chartjs, util) {
    var charts = {};

    var defaultChartConfig = {
        type: 'bar',
        options: {
            maintainAspectRatio: false,
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero:true
                    }
                }]
            },
            //title: {
            //    display: true,
            //    text: 'Custom Chart Title'
            //},
        }
    };

    function CubeVis(parent, opt_config) {
        var config = Object.assign({}, defaultChartConfig);
        var config = $.extend(true, config, opt_config);
        var canvas = $("<canvas>");
        $(parent).append(canvas)
        this.vis = new Chart(canvas, config);
        this.values = {};
    }
    CubeVis.prototype = Object.create(util.Emitter.prototype);
    CubeVis.prototype.constructor = CubeVis;

    CubeVis.prototype.load = function(data) {
        // To update the data, modify the data array then call update.
        for( let i=0; i<data.datasets.length; i++ ) {
            var visDset = this.vis.data.datasets[i];
            var inDset = data.datasets[i];
            if( !visDset ) {
                this.vis.data.datasets[i] = inDset;
            } else {
                visDset.data = inDset.data;
            }
        }
        if( data.labels ) {
            this.vis.data.labels = data.labels;
        }
        this.vis.update();
    }

//    CubeVis.prototype.values = function(values) {
//        if( typeof(values) === "undefined" ) {
//            return this.values;
//        } else {
//        }
//    }

    return CubeVis;
});