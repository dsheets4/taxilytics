define([
    "js/3rdparty/d3"
],
function(d3) {

    // Takes two objects: The first is the object to manipulate and the second defines
    // a function to call and the arguments to use.  The arguments can be either a scalar
    // of a single argument or an array of arguments.
    function applySettings(obj, settings) {
        if( settings ) {
            for( let f in settings ) {
                if( settings[f] instanceof Array ) {
                    obj[f].apply(obj, settings[f]);
                } else {
                    obj[f].call(obj, settings[f]);
                }
            }
        }
    }

    var Chart = function(opts){
        var self = this;

        // Handle options
        opts = opts || {};
        this.margin = opts.margin || {};
        this.margin.top = this.margin.top || 20;
        this.margin.bottom = this.margin.bottom || 20;
        this.margin.left = this.margin.left || 30;
        this.margin.right = this.margin.right || 10;
        this.svgDims = {};
        this.chartDims = {};
        this.chartClasses = opts.classes || "chart";
        this.xName = opts.xName || "X-Axis";
        this.yName = opts.yName || "Y-Axis";
        this.yFormat = opts.yFormat;
        this.xFormat = opts.xFormat;
        this.xDomain = opts.xDomain;
        this.yDomain = opts.yDomain;
        this.x = opts.x;
        this.y = opts.y || function(d) { return d; };
        this.onbrushend = opts.onbrushend;

        this.element = opts.element || document.createElement("div");

        this.svg = d3.select(this.element)
            .append("svg")
              .attr("class", this.chartClasses);
        this.chart = this.svg.append("g");
        this.drawArea = this.chart.append("g")
            .attr("class", "draw-area");

        if( opts.xScale ) {
            if( typeof(opts.xScale) === "string" ) {
                // Supports Time, Utc, Band, Ordinal, Linear, Pow (Power), Log, Sequential,
                // Quantize, Quantile, Threshold, and Point.
                var scaleStr = "scale" + opts.xScale;
                this.xScale = d3[scaleStr]();
                if( opts.xScale == "Time" || opts.xScale == "Utc" ) {
                    this.xScale.nice();
                }
            } else {
                this.xScale = opts.xScale;
            }
        } else {
            this.xScale = d3.scaleLinear();
        }
        this.yScale = opts.yScale || d3.scaleLinear();

        applySettings(this.xScale, opts.xScaleSettings);
        applySettings(this.yScale, opts.yScaleSettings);

        this.xAxis = d3.axisBottom(this.xScale)
            .ticks(5);
        this.xAxisGroup = this.chart.append("g")
            .attr("class", "x axis");
        this.xAxisGroup.append("text")
            .attr("dx", "1.5em")
            .attr("dy", "1.5em")
            .style("text-anchor", "end");

        this.yAxis = d3.axisLeft(this.yScale);
        this.yAxisGroup = this.chart.append("g")
            .attr("class", "y axis");
        this.yAxisGroup.append("text")
            .attr("dx", "-.5em")
            .attr("dy", "-.5em")
            .style("text-anchor", "end");

        this.brush = d3.brushX()
            .on("brush end", function() {
                if (d3.event.sourceEvent && d3.event.sourceEvent.type === "zoom")
                    return; // ignore brush-by-zoom
                if( self.onbrushend ) {
                    var selRange = d3.event.selection || self.xScale.range();
                    var extents = selRange.map(self.xScale.invert, self.xScale);
                    self.onbrushend(extents);
                }
            });
        this.brushG = this.drawArea.append("g")
            .attr("class", "brush");

        this.drawStrategy = new opts.drawStrategy(this.drawArea);
        this.setOptions(opts);
        this.setData([])
        this.resize();
    }

    Chart.prototype.setOptions = function(opts) {
        if( typeof(opts) !== "undefined" ) {
            if( typeof(opts.y) === "function" ) {
                this.y = opts.y;
            }
            if( typeof(opts.x) === "function" ) {
                this.x = opts.x;
            }
            if( typeof(opts.width) === "function" ) {
                this.width = opts.width;
            }
            if( typeof(opts.key) === "function" ) {
                this.key = opts.key;
            }
            if( typeof(opts.xFormat) === "function" ) {
                this.xFormat = opts.xFormat;
                this.xAxis.tickFormat(this.xFormat);
            }
            if( typeof(opts.yFormat) === "function" ) {
                this.yFormat = opts.yFormat;
                this.yAxis.tickFormat(this.yFormat);
            }
            if( typeof(opts.yName) === "string" ) {
                this.yName = opts.yName;
                this.setYName(this.yName);
            }
            if( typeof(opts.xName) === "string" ) {
                this.xName = opts.xName;
                this.setYName(this.yName);
            }
        }

        this.drawStrategy.options(opts);
    }

    Chart.prototype.setYName = function(name) {
        this.yAxisGroup.select("text").text(name);
    }

    Chart.prototype.setXName = function(name) {
        this.xAxisGroup.select("text").text(name);
    }

    Chart.prototype.setData = function(data) {
        if( this.xDomain instanceof Array ) {
            this.xScale.domain(this.xDomain);
        } else {
            if( this.width ) {
                var xMin = d3.min(data, this.x);
                if( isNaN(xMin) ) { xMin = 0; }
                this.xScale.domain([xMin, +xMin+(+d3.sum(data, this.width))]);
            } else {
                this.xScale.domain(data.map(this.x));
            }
        }
        if( this.yDomain instanceof Array ) {
            this.yScale.domain(this.yDomain);
        } else {
            this.yScale.domain([0, d3.max(data, this.y)]);
        }

        this.drawStrategy.data(data);
        this.refresh();
    }

    Chart.prototype.resize = function() {
        // Calculate space available for the chart.
        var styles = getComputedStyle(this.svg.node().parentElement);
        var rect = this.svg.node().parentElement.getBoundingClientRect();
        this.svgDims.width = rect.width - (
            parseInt(styles["padding-left"]) + parseInt(styles["padding-right"]) +
            parseInt(styles["margin-left"]) + parseInt(styles["margin-right"]) +
            parseInt(styles["border-left-width"]) + parseInt(styles["border-right-width"])
        );
        this.chartDims.width = this.svgDims.width - (this.margin.left + this.margin.right);
        this.svgDims.height = rect.height - (
            parseInt(styles["padding-top"]) + parseInt(styles["padding-bottom"]) +
            parseInt(styles["margin-top"]) + parseInt(styles["margin-bottom"]) +
            parseInt(styles["border-top-width"]) + parseInt(styles["border-bottom-width"])
        );
        this.chartDims.height = this.svgDims.height - (this.margin.top + this.margin.bottom);
        //if( this.chartDims.height < 100 ) { this.chartDims.height = 100; }
        //if( this.chartDims.width < 100 ) { this.chartDims.width = 100; }

        // Set chart size and scale ranges.
        this.svg
            .attr("width", this.svgDims.width)
            .attr("height", this.svgDims.height);
        this.chart
            .attr("transform", "translate(" + this.margin.left + "," + this.margin.right + ")");
        this.xScale
            .range([0, this.chartDims.width]);
        this.yScale
            .range([this.chartDims.height, 0]);

        this.brush
            .extent([[0, 0], [this.chartDims.width, this.chartDims.height]]);
        this.brushG
            .call(this.brush)
            .call(this.brush.move, this.xScale.range());

        this.refresh();
    }

    Chart.prototype.refresh = function() {
        var self = this;

        // Update axis now that domain is present on the scales.
        this.xAxis.scale(this.xScale);
        if( typeof(this.chartDims.height) !== "undefined" ) {
            this.xAxisGroup.attr("transform", "translate(0," + (this.chartDims.height) + ")");
        }
        this.yAxis.scale(this.yScale);

        this.xAxis
            .tickFormat(this.xFormat);
        if( this.rotateX ) {
            this.xAxisGroup
                .call(this.xAxis)
              .selectAll(".tick text")
                .style("text-anchor", "end")
                .attr("transform", "rotate(-15)");
        } else {
            this.xAxisGroup
                .call(this.xAxis)
        }
        this.yAxisGroup.call(this.yAxis);
        this.setXName(this.xName);
        this.setYName(this.yName);

        this.drawStrategy.draw(this);
    }

    return Chart;
});
