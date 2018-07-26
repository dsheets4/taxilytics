define([
    'js/3rdparty/d3'
],
function(d3) {
    //============================================================================
    function Margin(top,bottom,left,right) {
        if(typeof(top)    === "undefined") top    = 10;
        if(typeof(bottom) === "undefined") bottom = 10;
        if(typeof(left)   === "undefined") left   = 10;
        if(typeof(right)  === "undefined") right  = 10;

        this.top    = top;
        this.right  = right;
        this.bottom = bottom;
        this.left   = left;
    }

    //============================================================================
    function Dimensions(w,h) {
        if(typeof(w) === "undefined" || typeof(h) === "undefined") {
            var dims = getPageDims();
            if(typeof(w) === "undefined") {
                w = dims.x;
            }
            if(typeof(h) === "undefined") {
                h = dims.y;
            }
        }

        this.w = +w;
        this.h = +h;
    }


    //============================================================================
    function FillPattern() {

        this.path         = "M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2";
        this.w            = 4;
        this.h            = 4;
        this.stroke       = "#000000";
        this.stroke_width = 1;

        this.generate = function(parent, name) {
            parent
            .append("pattern")
            .attr("id",           name)
            .attr("patternUnits", "userSpaceOnUse")
            .attr("width",        this.w)
            .attr("height",       this.h)
            .append("path")
            .attr("d",            this.path)
            .attr("stroke",       this.stroke)
            .attr("stroke-width", this.stroke_width);
        };
    }

    //============================================================================
    function FillGradient() {

        this.orientation = {x1:"0%",y1:"0%",x2:"0%",y2:"100%"};
        this.stops = [{offset:"0%",color:"#FF6"},{offset:"100%",color:"#F60"}];

        this.generate = function(parent, name) {
            var grad = parent.append("linearGradient")
            .attr("id", name)
            .attr("x1", this.orientation.x1)
            .attr("y1", this.orientation.y1)
            .attr("x2", this.orientation.x2)
            .attr("y2", this.orientation.y2);

            for( let i in this.stops) {
                grad.append("stop")
                .attr("offset",     this.stops[i].offset)
                .attr("stop-color", this.stops[i].color);
            }
        };

    }

    //============================================================================
    // TODO: This class is incomplete.
    function ChartAxis() {

        this.axis     = {x:null,y:null};
        this.orient   = "left";
        this.g        = null;
        this.outline  = null;
        this.bar      = null;

        this.generate = function(parent, name, scale) {
            this.axis.y = d3.svg.axis()
            .scale(scale)
            .orient(this.orient);

            this.g = this.chart.append("g")
            .attr("class", "axis");

            this.bar = this.g
            .append("rect")
            .attr("x",      (xBarOffset))
            .attr("y",      this.drawHeight)
            .attr("width",  (this.axisWidthY-xBarOffset))
            .attr("height", 0)
            .attr("fill-opacity", 0.5);
        };

        this.transform = function(sCommand) {
            if( this.g ) {
                this.g.attr("transform", sCommand);
            }
        };
    }

    //============================================================================
    function ChartConfig(dims,m) {

        // Overall dimensions of the SVG object.
        if(!(dims instanceof Dimensions)) {
            if(!(typeof(dims) === "undefined")) {
                console.log("Bad type for dimensions in ChartConfig");
            }
            dims = new Dimensions();
        }
        this.dims = dims;

        // Margins
        if(!(m instanceof Margin)) {
            if(!(typeof(m) === "undefined")) {
                console.log("Bad type for margin in ChartConfig");
            }
            m = new Margin();
        }
        this.margin = m;

        // Chart area (total SVG size minus margins)
        this.chart = new Dimensions(
            ((this.dims.w - this.margin.left) - this.margin.right),
            ((this.dims.h - this.margin.top)  - this.margin.bottom) );
    }

    //============================================================================
    function ChartProperty(key, value) {
        this.key   = key;
        this.value = value;
    }

    //============================================================================
    //Generic chart object
    function ElementConfig(sName, sUnits, styleClass, options, props) {
        if(typeof(styleClass) === "undefined") styleClass = "line";
        if(typeof(props)      === "undefined") props      = [];

        this.name       = sName;
        this.units      = sUnits;
        this.styleClass = styleClass;
        this.options    = JSON.parse(JSON.stringify(options));
        this.props      = props;
    };


    //============================================================================
    function Line(parentRect, data, scale, config) {

        // -------------------------------------------------------------------------
        // Verify arguments.

        // -------------------------------------------------------------------------
        // Members
        this.data  = data;
        this.scale = {x:null,y:null};
        this.axis  = {x:null,y:null};
        this.line  = null;
        this.points = null;
        this.config = config;

        this.g = parentRect.append("g")
            .attr("name", this.config.name);
    }

    Line.prototype = Object.create(null);
    Line.prototype.constructor = Line;

    Line.prototype.update = function(data) {
        var self = this;

        this.path = this.g.selectAll("path." + this.config.styleClass)
            .data([data]);
        // Updated existing points
        this.path
            .attr("class", this.config.styleClass)
            .attr("d", this.line);
        // Creates and sets data for new points.
        this.path
            .enter().append("path")
            .attr("class", this.config.styleClass)
            .attr("d", this.line);
        this.path
            .exit().remove();

        if( this.config.options.Points ) {
            this.points = this.g.selectAll("circle")
                .data(data);
            console.log("Update", this.points)
            this.points
                .attr("cx", function(d) { return scaleX(d.time); })
                .attr("cy", function(d) { return self.scale.y(d.value); })
                .attr("r",  2)
                .attr("stroke-width", 1);
            this.points
                .enter().append("circle")
                .attr("cx", function(d) { return scaleX(d.time); })
                .attr("cy", function(d) { return self.scale.y(d.value); })
                .attr("r",  2)
                .attr("stroke-width", 1);
            this.points
                .exit().remove();
        }
        // Apply specific properties for this line (e.g. dash pattern).
        for( i in this.config.props ) {
            //console.log( "Setting line property: " + this.config.props[i].key + "=" + this.config.props[i].value);
            this.path.attr( this.config.props[i].key, this.config.props[i].value );
            if( this.config.props[i].key == "stroke" ) {
                this.axis.y.attr  ( this.config.props[i].key, this.config.props[i].value);
                this.axis.bar.attr( "fill",               this.config.props[i].value);
                if( this.config.options.Points) {
                    this.points.attr  ( "fill",               this.config.props[i].value);
                    this.points.attr  ( this.config.props[i].key, this.config.props[i].value);
                }
            }
            if( this.config.props[i].key == "stroke-width" ) {
                if( this.config.options.Points) {
                    this.points.attr ( this.config.props[i].key, this.config.props[i].value);
                }
            }
        }
    }

    //============================================================================
    //TODO: Pan and zoom
    //TODO: Markers over events with a tooltip to give info
    //TODO: Gradient and pattern generator functions (function that generates the defs)
    //TODO: Pattern generator that provides color fill plus pattern
    //TODO: Single y-axis functionality
    //TODO: Controls to toggle lines and/or events to be displayed or not
    //TODO: Mouseover chart axis bar-chart with current values
    //TODO: Mouseover line with point highlight
    //TODO: Create a list of chart features where the object can be queried to dynamically create options controls
    //TODO: Mouse move events in the chart area trigger the mouseout when the mouse goes over a line (but not an event)
    function LineChart(parent_name, cfg) {

        //	-------------------------------------------------------------------------
        this.cfg;           // Chart configuration
        this.svg;           // Entire SVG area
        this.chart;         // Group representing chart area (where lines/events are drawn)
        this.lines  = [];   // Lines added to the chart
        this.events = [];   // Events added to the chart
        this.scale  = {x:undefined,y:undefined};
        this.axis   = {x:undefined,y:undefined};
        this.axis.xMarker = null;
        this.drawHeight;
        this.axisWidthY = 50;
        this.options = {
           outlines:false,
        };

        //	-------------------------------------------------------------------------
        this.setOption = function(sOption, value) {
           this.options[sOption] = value;
        };

        //	-------------------------------------------------------------------------
        this.axisMarginY = function() {
            return (this.lines.length)*this.axisWidthY;
        };

        //	-------------------------------------------------------------------------
        this.drawWidth = function() {
            return this.cfg.chart.w-this.axisMarginY();
        };

        //	-------------------------------------------------------------------------
       var drag = d3.behavior.drag()
       .origin(function(d) { return d; })
       .on("drag", dragmove);
       function dragmove(d) {
          d3.select(this)
          .attr("y1", d.y = d3.event.y)
          .attr("y2", d.y);
       }

        this.addHorizontalMarker = function() {
           d = [{x:this.scale.x.range()[0],y:this.drawHeight}];

           marker = this.draw.append("g")
               .attr("class", "horizontal_marker");

           marker
               .selectAll("line")
               .data(d)
               .enter().append("line")
               .attr("x1", this.scale.x.range()[0]-5)
               .attr("y1", function(d) { return d.y; })
               .attr("x2", this.scale.x.range()[1])
               .attr("y2", function(d) { return d.y; })
               .attr("stroke", "red")
               .attr("stroke-width", 3)
               .on("click", function() {
                   if (d3.event.defaultPrevented) return;
               })
               .call(drag);
        };

        //	-------------------------------------------------------------------------
        this.drawBarMarkers = function(bDraw, x, y) {
            if( !this.scale || !this.scale.x ) {
                return;
            }

            // This is the time where the indicator (e.g. mouse) is at.
            time = this.scale.x.invert(x);

            // Loop through each line to find the corresponding value of the y-axis
            // for each line.
            for( i in this.lines ) {
                line = this.lines[i];
                if( line.line ) {
                    var value = {time:this.scale.x.domain[0],value:line.scale.y.domain()[0]};
                    var valueUpper = value;
                    var valueLower = value;

                    var upper = Number.MAX_VALUE;
                    var lower = -Number.MAX_VALUE;
                    if( bDraw && time > line.scale.x.domain()[0] && time < line.scale.x.domain()[1] ) {
                        line.data.some(function(curr) {
                            if( time == curr.time ) {
                                value = curr;
                                return true;
                            }
                            else {
                                temp = curr.time.getTime() - time.getTime();
                                //console.log(temp);
                                if( temp < 0 && temp > lower ) {
                                    valueLower = curr;
                                    lower = temp;
                                }
                                if( temp >= 0 && temp < upper ) {
                                    valueUpper = curr;
                                    upper = temp;
                                }
                            }

                            prev = curr;
                        });

                        if( Math.abs(lower) < Math.abs(upper) ) {
                            value = valueLower;
                        } else {
                            value = valueUpper;
                        }

                        switch( line.config.options.AxisMarkerType ) {

                            case LineChart.AxisMarkerShape.BOUNDS:
                                if( valueLower.value < valueUpper.value ) {
                                    height = line.scale.y(valueLower.value)-line.scale.y(valueUpper.value);
                                    y = line.scale.y(valueUpper.value);
                                } else if (valueLower.value > valueUpper.value) {
                                    height = line.scale.y(valueUpper.value)-line.scale.y(valueLower.value);
                                    y = line.scale.y(valueLower.value);
                                } else {
                                    height = Math.min( this.drawHeight*.01,5);
                                    y = line.scale.y(value.value);
                                }
                                break;

                            case LineChart.AxisMarkerShape.BAR:
                                height = (this.drawHeight-line.scale.y(value.value));
                                y = line.scale.y(value.value);
                                break;

                            case LineChart.AxisMarkerShape.TICK:
                            default:
                                height = Math.min( this.drawHeight*.01,5);
                                y = line.scale.y(value.value);
                                break;
                        }
                        line.axis.bar
                        .transition()
                        .duration(50)
                        .attr("height", height)
                        .attr("y",      y);
                        line.axis.value
                        .text(value.value.toFixed(2));

                        //this.axis.xMarker
                        //   .text(time);
                    } else {
                        line.axis.bar
                        .attr("y",      this.drawHeight)
                        .attr("height", 0);
                        line.axis.value
                        .text("N/A");
                    this.axis.xMarker
                        .text("");
                    }
                }
            }
        };

        //	-------------------------------------------------------------------------
        //	This function applies a couple very basic things that D3 can do in regard
        //	to manipulating the HTML page and simple visuals.
        this.create = function (parent_name, cfg) {

            // Save the configuration.  Note that if the
            this.cfg = cfg;
            this.drawHeight = cfg.chart.h-20; // Room for x-axis ticks.

            // Create the SVG object within the HTML.
            this.svg = d3.select(parent_name).append("svg")
            .attr("class", "line_chart")
            .attr("width", cfg.dims.w)
            .attr("height", cfg.dims.h);

            // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            // Predefined fill patterns
            var defs = this.svg.append("defs");

            // Hatch
            var fill = new FillPattern();
            fill.generate(defs, "diagonalHatch");

            var grad = new FillGradient();
            grad.generate(defs, "gradient1");

            // Useful reference when working on the layout.
            if( this.options.outlines ) {
                g = this.svg.append("g")
                .attr("class", "outlines");
                g.append("rect")
                .attr("id", "svg_dims")
                .attr("x",      0)
                .attr("y",      0)
                .attr("width",  this.cfg.dims.w)
                .attr("height", this.cfg.dims.h)
                .attr("fill", "none")
                .attr("stroke", "black")
                .attr("stroke-width", 2);

                g.append("rect")
                .attr("x",      this.cfg.margin.left)
                .attr("y",      this.cfg.margin.top)
                .attr("width",  this.cfg.chart.w)
                .attr("height", this.cfg.chart.h)
                .attr("fill", "none")
                .attr("stroke", "blue")
                .attr("stroke-width", 1);
            }


            // Create a chart area, which is where all lines and events will be drawn.
            this.chart = this.svg.append("g")
            .attr("class", "chart_area")
            .attr("transform", "translate(" + this.cfg.margin.left + "," + this.cfg.margin.top + ")");


            // This second layer group "anchors" the chart in the transform that
            // accounts for the margin above.  Translations on the chart are in
            // a different coordinate system starting at a new origin.
            // Note that d3.mouse provides the coordinates of the object detecting
            // the mouse event, which is conveniently the draw area of the chart.
            this.draw = this.chart
            .append("g")
            .attr("class", "draw_area")
            .datum(this)
            .on("mousemove", function() {
                if( (this.__data__ instanceof LineChart) ) {
                    this.__data__.drawBarMarkers(true, d3.mouse(this)[0],d3.mouse(this)[1]);
                }
            })
            .on("mouseout", function() {
                if( (this.__data__ instanceof LineChart) ) {
                    this.__data__.drawBarMarkers(false);
                }
            });

            // This rect is used so that mouse move in the draw area can
            // be detected.  If there's not object then the events aren't
            // ever triggered.
            this.drawRect = this.draw.append("rect")
            .attr("x",      0)
            .attr("y",      0)
            .attr("width",  this.cfg.chart.w)
            .attr("height", this.drawHeight)
            .attr("fill", "white")
            .attr("fill-opacity", 0)
            .attr("stroke", "none");

            if( this.options.outlines ) {
                this.drawRect
                .attr("stroke", "yellow")
                .attr("stroke-dasharray", "10,3")
                .attr("stroke-width", 3);
            }

            // Create an events layer in the chart.  This will result in events drawn
            // behind the lines since the group is added before the lines.
            this.eventGroup = this.draw.append("g")
            .attr("class", "event");
        };
        this.create(parent_name, cfg);

        //	-------------------------------------------------------------------------
        nAddTransTimeMs = 0;
        this.updateXAxis = function(data) {
            var domain = [
                d3.min(data, function(d) { return d.time; } ),
                d3.max(data, function(d) { return d.time; } )
            ];
            // TODO: This bit of code is intended to preserve the domains for ALL lines.
            //       Need to store the separate domains and then update the one corresponding
            //       to the line being updated and then construct the total domain from that.
            //       For now we only need one line.
            //if( this.scale.x ) {
            //    domain = [
            //        Math.min(this.scale.x.domain()[0], domain[0]),
            //        Math.max(this.scale.x.domain()[1], domain[1])
            //    ];
            //}

            // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            // If this is the first line, the scale for the x axis is undefined, create it
            // Else this is a subsequent line and we just need to update and transition.
            if( !this.scale.x ) {
                this.scale.x = d3.time.scale()
                    .range([0, this.drawWidth()])
                    .domain(domain);

                var xAxis = d3.svg.axis()
                    .scale(this.scale.x)
                    .orient("bottom");

                // x-axis is added to the draw group and then it will automatically translate
                // to the appropriate position based on the number of y-axes.
                this.axis.x = this.draw.append("g")
                    .attr("class", "x axis")
                    .attr("transform", "translate(0," + this.drawHeight + ")")
                    .call(xAxis);

                this.axis.xMarker = this.axis.x
                    .append("text")
                    .attr("y", 15)
                    .text("");
            } else {
                // The domain is the data min,max.  When adding a new line we must determine
                // if the data in the new line changes the extents of the domain so we find
                // the min and max in the new data and then determine if that modifies the
                // domain.  The range is the window size, which has also shrunk.
                currDomain = this.scale.x.domain();
                this.scale.x
                    .range([0,this.cfg.chart.w-(this.axisMarginY())])
                    .domain(domain);

                // Create a new x axis in D3 with the updated domain (extents)
                var xAxis = d3.svg.axis()
                    .scale(this.scale.x)
                    .orient("bottom");

                // This will transition the x-axis to use any new tick marks based on the new
                // range and domain.
                this.axis.x
                    .transition()
                    .duration(nAddTransTimeMs)
                    .call(xAxis);
            }

            // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            // Update existing elements (e.g. lines and events) to new scale

            // Since the draw area was shrunk to allow for the new y-axis, the previous
            // lines (i.e. the ones already drawn) must be moved according to the new
            // x-axis information.
            scaleX = this.scale.x;
            for( i in this.lines ) {
                line = this.lines[i];
                line.scale.x = this.scale.x;
                if( line.line ) {
                    line.line
                    .x(function(d) { return scaleX(d.time); })
                    .y(function(d) { return line.scale.y(d.value); });
                    line.path
                    .transition()
                    .duration(nAddTransTimeMs)
                    .attr("d", line.line);
                }
                if( line.config.options.Points && line.points ) {
                    line.points
                        .transition()
                        //.delay(function(d, i) { return i*(nAddTransTimeMs/line.data.length); })
                        .duration(nAddTransTimeMs)
                        .attr("cx", function(d) { return scaleX(d.time); })
                        .attr("cy", function(d) { return line.scale.y(d.value); });
                }
            }

            scaleX = this.scale.x;
            for( i in this.events ) {
                this.events[i]
                    .transition()
                    .duration(nAddTransTimeMs)
                    .attr("x",      function(d)    { return scaleX(d.time); })
                    .attr("width",  function(d)    { return scaleX(d.time.getTime()+d.durationMs) - scaleX(d.time); });
            }

        };

        //	-------------------------------------------------------------------------
        this.addLine = function (data, lineCfg) {

            var newline = new Line(this.draw, data, {x:null,y:null}, lineCfg);
            this.lines.push( newline );

            // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            // Input processing

            // Verify arguments.
            if( !(lineCfg instanceof ElementConfig) ) {
                if( !(typeof(lineCfg) === "undefined") ) {
                    console.log("Bad type for ElementConfig in createLine");
                }
                lineCfg = new ElementConfig("test", undefined, undefined, {});
            }

            // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            // Update x-axis and existing elements (lines, events, ..) to new scale
            this.updateXAxis(data);

            // If in options.outlines, redraw the "draw" area outline
            if( this.options.outlines ) {
                this.drawRect
                    .transition()
                    .duration(nAddTransTimeMs)
                    .attr("width", this.drawWidth());
            }

            // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            // Y-axis

            // Move the chart area to create room for the new independent axis.
            this.draw.transition()
                .duration(nAddTransTimeMs)
                .attr("transform", "translate(" + this.axisMarginY() + "," + 0 + ")");

            // TODO: Allow line chart to have a common y-axis
            //       Above we did a bunch of calculations to place the data in a new
            //       x-axis.  Ultimately we want to allow for both independent and
            //       common y-axis.  The rescaling logic will need to be an event handler
            //       for that so look at what common functions might help drive this.

            // Create a new (independent) y-axis for the new line data.
            newline.scale.y = d3.scale.linear()
                .range([this.drawHeight, 0])
                .domain(d3.extent(data, function(d) { return d.value; }));

            var yAxis = d3.svg.axis()
                .scale(newline.scale.y)
                .orient("left");

            newline.axis.g = this.chart.append("g")
                .attr("class", "y axis")
                .attr("transform", "translate(" + this.axisMarginY() + ",0)");

            var g = newline.axis.g.append("g")
                .attr("transform", "translate(" + -this.axisWidthY + ",0)");

            // Create the current mouse value bar in the axis.
            var xBarOffset = 15;
            newline.axis.bar = g
                .append("rect")
                .attr("x",      (xBarOffset))
                .attr("y",      this.drawHeight)
                .attr("width",  (this.axisWidthY-xBarOffset))
                .attr("height", 0)
                .attr("fill-opacity", 0.5);
            newline.axis.y = newline.axis.g
                .call(yAxis);
            newline.axis.y.append("text")
                .attr("transform", "rotate(-90)")
                .attr("y", 12)
                .style("text-anchor", "end")
                .text(lineCfg.name + " (" + lineCfg.units + ")");

            newline.axis.value = newline.axis.g
                .style("text-anchor", "end")
                .append("text")
                .attr("y", this.drawHeight+15);

            // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            // Add the line to the chart
            scaleX = this.scale.x;
            newline.line = d3.svg.line()
                .x(function(d) { return scaleX(d.time); })
                .y(function(d) { return newline.scale.y(d.value); });

            newline.update(data);

            return newline;
        };

        //	-------------------------------------------------------------------------
        this.addEvent = function (data, cfg) {
            // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            // Input processing

            // Verify arguments.
            if( !(cfg instanceof ElementConfig) ) {
                if( cfg && !(typeof(cfg) === "undefined") ) {
                    console.log("Bad type for ElementConfig in createLine");
                }
                cfg = new ElementConfig("test");
            }

            // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            // Update x-axis and existing elements (lines, events, ..) to new scale
            domain = [
                d3.min(data, function(d) { return d.time; } ),
                d3.max(data, function(d) { return d.time.getTime()+d.durationMs; } )
            ];
            if( this.scale.x ) {
                domain = [
                    Math.min(this.scale.x.domain()[0], domain[0]),
                    Math.max(this.scale.x.domain()[1], domain[1])
                ];
            }
            this.updateXAxis(domain);


            // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            // Add new event to the draw area

            var scaleX = this.scale.x;

            newevent = this.eventGroup
                .append("g")
                .selectAll("rect")
                .data(data)
                .enter()
                .append("rect")
                .attr("x",      function(d)    { return scaleX(d.time); })
                .attr("y",      0)
                .attr("rx",     5)
                .attr("ry",     5)
                .attr("width",  function(d)    { return scaleX(d.time.getTime()+d.durationMs) - scaleX(d.time); })
                .attr("height", this.drawHeight);

            // Apply specific properties for this event.
            for( i in cfg.props ) {
                newevent.attr( cfg.props[i].key, cfg.props[i].value );
            }

            this.events.push(newevent);
        };
    };

    //	-------------------------------------------------------------------------
    LineChart.AxisMarkerShape = Object.freeze({TICK: 0, BOUNDS: 1, BAR: 2});
    LineChart.AxisMarkerValue = Object.freeze({CLOSEST: 0});

    return {
        Margin: Margin,
        Dimensions: Dimensions,
        FillPattern: FillPattern,
        FillGradient: FillGradient,
        ChartAxis: ChartAxis,
        ChartConfig: ChartConfig,
        ChartProperty: ChartProperty,
        ElementConfig: ElementConfig,
        Line: Line,
        LineChart: LineChart
    }
});