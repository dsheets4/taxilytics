define([
    "js/vis/chart",
    "js/3rdparty/d3",
],
function(Chart, d3) {

    var LineChart = function(drawArea, opts){

        var self = this;

        // Handle options
        opts = opts || {};
        this.options(opts);

        this.bars = drawArea.append("g")
            .attr("class", "line")
    }

    LineChart.prototype.options = function(opts) {
        if( typeof(opts) !== "undefined" ) {
            if( typeof(opts.width) === "function" ) {
                this.width = opts.width;
            }
            if( typeof(opts.key) === "function" ) {
                this.key = opts.key;
            }
        }
    }

    LineChart.prototype.data = function(data) {
        console.log("Line Draw:", data);
        this.line = this.bars.selectAll("path")
            .data(data, this.key);
    }

    LineChart.prototype.draw = function(self) {

        // Create a bar for each datum
        this.line.exit().remove();
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
        }
        update.call(this, this.line);
        update.call(this, this.line.enter().append("path")
            .attr("class", "line")
            .on("mouseover", function(){ d3.select(this).classed("highlight", true); })
            .on("mouseout", function(){ d3.select(this).classed("highlight", false); })
        );
    }

    return LineChart;
});