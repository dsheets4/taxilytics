define([
    "js/vis/chart",
    "js/3rdparty/d3",
],
function(Chart, d3) {

    var BarChart = function(drawArea, opts){

        var self = this;

        // Handle options
        opts = opts || {};
        this.options(opts);

        this.bars = drawArea.append("g")
            .attr("class", "bar");

        this.line = d3.line();
    }

    BarChart.prototype.options = function(opts) {
        if( typeof(opts) !== "undefined" ) {
            if( typeof(opts.width) === "function" ) {
                this.width = opts.width;
            }
            if( typeof(opts.key) === "function" ) {
                this.key = opts.key;
            }

            if( typeof(opts.x) === "function" ) {
                this.line.x(opts.x);
            }

            if( typeof(opts.y) === "function" ) {
                this.line.y(opts.y);
            }
        }
    }

    BarChart.prototype.data = function(data) {
        this.bar = this.bars.selectAll("rect")
            .data(data, this.key);
    }

    BarChart.prototype.draw = function(self) {

        // Create a bar for each datum
        this.bar.exit().remove();
        function update(selection) {
            var x, w;
            selection
                .attr("x", function(d, i, arr) {
                    if( self.width ) {
                        return self.xScale(self.x(d, i, arr));
                    } else {
                        return (self.chartDims.width / arr.length) * i;
                    }
                })
                .attr("width", function(d, i, arr) {
                    if( self.width ) {
                        return self.xScale(+self.width(d, i, arr) + (+self.xScale.invert(0)));
                    } else {
                        return self.chartDims.width / arr.length;
                    }
                })
                .attr("y", function(d, i) { return self.yScale(self.y(d, i)); })
                .attr("height", function(d) {
                    return self.chartDims.height - self.yScale(self.y(d))
                })
                selection
                    .attr("fill", "none")
                    .attr("stroke", "steelblue")
                    .attr("stroke-linejoin", "round")
                    .attr("stroke-linecap", "round")
                    .attr("stroke-width", 1.5)
                    .attr("d", this.line);
        }
        update.call(this, this.bar);
        update.call(this, this.bar.enter().append("rect")
            .attr("class", "bar")
            .on("mouseover", function(){ d3.select(this).classed("highlight", true); })
            .on("mouseout", function(){ d3.select(this).classed("highlight", false); })
        );
    }

    return BarChart;
});
