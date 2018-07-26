define([
    "streetcube/js/cube",
    "streetcube/js/vis",
    "js/util",
    "js/map/heatmap",
],
function(cube, vis, util, heatmap) {
    var view = {};

    // Maps the HTML tags to constants.
    selector = {
        map: "#map",
        hourly: "#hours",
        daily: "#days",
        summary: "#summary",
        highway: "#highway",
    };

    function CubeView() {
        var self = this;
        this._cube = null;
        this._extents = null;
        this.availableCategories = {};

        this.events = {
            "timeSelectAbsolute": new util.EventObject(),
            "timeSelectDays": new util.EventObject(),
            "timeSelectHours": new util.EventObject(),
            "categorySelection": new util.EventObject(),
            "regionSelection": new util.EventObject(),
            "userSelection": new util.EventObject(),
        };
    };
    CubeView.prototype = Object.create(util.Emitter.prototype);
    CubeView.prototype.constructor = CubeView;

    CubeView.prototype.setAvailableCategoryValues = function(values) {
        var columns = [];
        for( let i=0; i<values.length; i++ ) {
            this.availableCategories[values[i]] = false;
        }
        console.log(this.availableCategories);
    }

    CubeView.prototype.setInitialCategoryValues = function(values) {
        for( let i=0; i<values.length; i++ ) {
            this.availableCategories[values[i]] = true;
        }
    }

    CubeView.prototype.create = function() {
        var self = this;
        this.selectedCategories = {};
        this.availableCategories = [];

        this.hourly = new vis.CubeVis(selector.hourly, {
            data: {
                labels: [
                    "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11",
                    "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23",
                ],
                datasets: []
            },
            options: {
                legend: {
                    display: false,
                },
            }
        });

        this.daily = new vis.CubeVis(selector.daily, {
            data: {
                labels: ["Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sun"],
                datasets: []
            },
            options: {
                legend: {
                    display: false,
                },
            }
        });

        this.summary = new vis.CubeVis(selector.summary, {
            data: {
                labels: [],
                datasets: []
            },
            options: {
                legend: {
                    position: 'bottom',
                    display: true,
                },
                scales: {
                    xAxes: [{
                        type: 'time',
                        ticks: {
                            maxRotation: 0,
                        }
                    }]
                },
                brush: {
                    mode: 'x',
                    onSelect: function(range) {
                        self.emit("timeSelectAbsolute", range);
                    }
                }
            }
        });

        var visibleColumns = function(columns) {
            this.hide();
            columns.forEach(function(d) {
                this.show(d);
            }, this);
        }

        function mouseover(id) {
            if (!this.transiting && this.isTargetToShow(id)) {
            }
        }

        function mouseout(id) {
        }

        function click(id) {
            var catEvent = {
                highway: {}
            }
            // Use !this.isTargetToShow(id) because the first toggle hasn't happened yet.
            catEvent.highway[id] = (!this.isTargetToShow(id));
            self.emit("categorySelection", catEvent);
        }

        this.map = new vis.Map($(selector.map).attr("id"), {
            // TODO: Link colors from chart to map.
            //colorTable: this.summaryChart.data.colors()
            onSelection: function(features) {
                self.emit("userSelection", [features]);
            }
        });

        var val = 0;
        this.heatLayer = new heatmap(
            function(f) {
                return Math.random();
            },
            {
                threshold_normal: 0.15,
                threshold_invert: 0.80,
            }
        );

        this.map.getLayers().push(new ol.layer.Group({
                title: "Road Type Heatmap",
                layers: [
                    this.heatLayer.heatLayer,
                    this.heatLayer.streetLayer,
                ]
            })
        );

        var mapTimerPending = false;
        function emitExtents() {
            mapTimerPending = false;
            self.emit("regionSelection", [self.map.getViewExtent()]);
        }
        this.map.getView().on("propertychange", function(e) {
            if( !mapTimerPending ) {
                mapTimerPending = true;
                setTimeout(emitExtents, 500);
            }
            switch(e.key) {
                case "resolution":
                    self.heatLayer.regenerate(e.target.get(e.key));
                    break;
                // case "center":
                //    heatLayer.regenerate(self.map.getView().getResolution());
                //    break;
            }
        });
    }

    view.CubeView = CubeView;
    return view;
});