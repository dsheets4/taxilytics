
define(['Chart', "js/util"],
function(Chart, util) {
    Chart.defaults.global.events.push('mousedown');
    Chart.defaults.global.events.push('mouseup');

    var brushMode = {
        rightEdge: 1,
        pan: 2,
        leftEdge: 3,
    }

    var brushes = {};

    brushes.BrushX = function BrushX(options) {
        options = options || {};
        this.brushMode = null;
        this.handleDims = {
            width: 10,
            height: 20
        };
        this.axisId = options.axisId || 'x-axis-0';

        this.events = {
            "timeSelection": new util.EventObject(),
        };
        this.eventThrottle = false;
        if( options.onSelect ) {
            this.on('timeSelection', options.onSelect);
        }
    }
    brushes.BrushX.prototype = Object.create(util.Emitter.prototype);
    brushes.BrushX.prototype.constructor = brushes.BrushX;

    brushes.BrushX.prototype.calculateSize = function(ci /*chartInstance*/) {
        var minVal = ci.scales[this.axisId].firstTick;
        var maxVal = ci.scales[this.axisId].lastTick;
        if( !this.extents ) {
            this.extents = [];
            this.extents[0] = minVal;
            this.extents[1] = maxVal;

            this.dims = {};
        }

        // Clamp to chart - Note: Time scale uses a Moment.js object
        if( minVal._isAMomentObject ) {
            if( this.extents[0].isBefore(minVal) || this.extents[0].isAfter(maxVal) ) {
                this.extents[0] = minVal;
            }
            if( this.extents[1].isAfter(maxVal) || this.extents[1].isBefore(minVal) ) {
                this.extents[1] = maxVal;
            }
        } else {
            if( this.extents[0] < minVal || this.extents[0] > maxVal ) {
                this.extents[0] = minVal;
            }
            if( this.extents[1] > maxVal || this.extents[1] < minVal ) {
                this.extents[1] = maxVal;
            }
        }

        // Calculate brush dimensions.
        this.dims.x = ci.scales[this.axisId].getPixelForValue(this.extents[0]);
        this.dims.y = ci.chartArea.top;
        this.dims.width = ci.scales[this.axisId].getPixelForValue(this.extents[1]) - this.dims.x;
        this.dims.height = ci.chartArea.bottom - ci.chartArea.top;
    }

    brushes.BrushX.prototype.createBrushGrabBoxPath = function (ctx) {
        var centerY = this.dims.height / 2;
        ctx.beginPath();
        ctx.rect(this.dims.x, centerY, this.handleDims.width, this.handleDims.height);
        ctx.rect(
            this.dims.x + this.dims.width - this.handleDims.width,
            centerY,
            this.handleDims.width,
            this.handleDims.height
        );
        ctx.closePath();
        return centerY;
    }

    brushes.BrushX.prototype.draw = function(ctx) {
        ctx.save();
        ctx.fillStyle = 'rgba(0, 100, 255, 0.1)';
        ctx.strokeStyle = 'rgba(0, 0, 0, 0)';
        ctx.fillRect(this.dims.x, this.dims.y, this.dims.width, this.dims.height);

        // Pull handles for selection.
        ctx.fillStyle = 'rgba(0, 100, 255, 0.4)';
        var centerY = this.createBrushGrabBoxPath(ctx);
        ctx.fill();

        ctx.fillStyle = 'rgba(96, 96, 96, 0.6)';
        ctx.beginPath();
        var padding = 1;
        var x = this.dims.x + this.handleDims.width - padding;
        var base = this.handleDims.width - (padding*2);
        ctx.moveTo(x, centerY + padding);
        ctx.lineTo(x, centerY + this.handleDims.height - (padding*2));
        ctx.lineTo(x - base, centerY + (this.handleDims.height / 2));
        x = this.dims.x + this.dims.width - this.handleDims.width + padding;
        ctx.moveTo(x, centerY + padding);
        ctx.lineTo(x, centerY + this.handleDims.height - (padding*2));
        ctx.lineTo(x + base, centerY + (this.handleDims.height / 2));
        ctx.fill();

        ctx.restore();
    }

    brushes.BrushX.prototype.onMouseDown = function(ci /*chartInstance*/, event) {
        if (event.x > ci.chartArea.left && event.x < ci.chartArea.right) {
            var clickPtLt = ci.scales[this.axisId].getValueForPixel(event.x - this.handleDims.width);
            var clickPtRt = ci.scales[this.axisId].getValueForPixel(event.x + this.handleDims.width);
            if (clickPtLt.isBefore(this.extents[0])) {
                this.brushMode = brushMode.leftEdge;
            } else if (clickPtRt.isAfter(this.extents[1])) {
                this.brushMode = brushMode.rightEdge;
            } else {
                this.brushMode = brushMode.pan;
                this.brushMouseOffset = event.x - this.dims.x;
            }
            this.onMouseMove(ci, event);
        }
    }

    brushes.BrushX.prototype.onMouseMove = function(ci /*chartInstance*/, event) {
        if (this.brushMode) {
            switch (this.brushMode) {
                case brushMode.pan:
                    var newLt = event.x - this.brushMouseOffset;
                    var newRt = newLt + this.dims.width;
                    if (newLt < ci.scales[this.axisId].left) {
                        newLt = ci.scales[this.axisId].left;
                    }
                    if (newRt > ci.scales[this.axisId].right) {
                        newLt = ci.scales[this.axisId].right - this.dims.width;
                    }

                    this.dims.x = newLt;
                    this.extents[0] = ci.scales[this.axisId].getValueForPixel(this.dims.x);
                    this.extents[1] = ci.scales[this.axisId].getValueForPixel(this.dims.x + this.dims.width);
                    break;
                case brushMode.leftEdge:
                    var newLt = event.x;
                    if (newLt < ci.scales[this.axisId].left) {
                        newLt = ci.scales[this.axisId].left;
                    }
                    if( newLt > (this.dims.x + this.dims.width) ) {
                        newLt = (this.dims.x + this.dims.width);
                    }
                    this.dims.width += (this.dims.x - newLt);
                    this.dims.x = newLt;
                    this.extents[0] = ci.scales[this.axisId].getValueForPixel(this.dims.x);
                    break;
                case brushMode.rightEdge:
                    var newRt = event.x;
                    if (newRt > ci.scales[this.axisId].right) {
                        newRt = ci.scales[this.axisId].right;
                    }
                    if( newRt < this.dims.x ) {
                        newRt = this.dims.x;
                    }
                    this.dims.width = (newRt - this.dims.x);
                    this.extents[1] = ci.scales[this.axisId].getValueForPixel(this.dims.x + this.dims.width);
                    break;
            }
            if( !this.eventThrottle ) {
                this.eventThrottle = true;
                var self = this;
                setTimeout(function(){ self.eventThrottle = false;}, 400);
                this.emit("timeSelection", [[[this.extents[0].toDate(), this.extents[1].toDate()]]]);
            }
            ci.update();
        } else {
            var ctx = ci.chart.ctx;
            this.createBrushGrabBoxPath(ctx);
            if (ctx.isPointInPath(event.x, event.y)) {
                ci.chart.canvas.style.cursor = 'w-resize';
            } else {
                ci.chart.canvas.style.cursor = 'default';
            }
        }
    }

    brushes.BrushX.prototype.onMouseUp = function (chartInstance, event) {
        this.brushMode = null;
    }

    var plugin = {
        afterInit: function (chartInstance) {
            var options = chartInstance.options;
            if( options.brush ) {
                switch( options.brush.mode ) {
                    case 'x':
                        chartInstance.brush = new brushes.BrushX(options.brush);
                        break;
                }
            }
        },
        afterLayout: function (chartInstance) {
            if( chartInstance.brush ) {
                chartInstance.brush.calculateSize(chartInstance);
            }
        },
        afterDatasetsDraw: function (chartInstance, easing) {
            if( chartInstance.brush ) {
                var ctx = chartInstance.chart.ctx;
                chartInstance.brush.draw(ctx);
            }
        },
        afterEvent: function (chartInstance, event) {
            if( chartInstance.brush ) {
                switch(event.type) {
                case 'mousedown':
                    chartInstance.brush.onMouseDown(chartInstance, event);
                    break;
                case 'mouseup':
                    chartInstance.brush.onMouseUp(chartInstance, event);
                    break;
                case 'mousemove':
                    chartInstance.brush.onMouseMove(chartInstance, event);
                    break;
                }
            }
        },
    };

    Chart.plugins.register(plugin);
});