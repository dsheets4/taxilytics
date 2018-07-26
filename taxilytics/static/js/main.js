requirejs.config({
	// By default load any module IDs from static/js
	// TODO: Static is a hardcoded variable that should come from server framework
	baseUrl : '/static/',

	// paths: When a request for the key comes in, look in value instead.
	paths: {
	    // TODO: Choosing deployable ol vs. ol-debug would be nicer based on DEBUG mode
	    "js/3rdparty/ol": "js/3rdparty/ol-debug",
	    "js/3rdparty/d3": "js/3rdparty/d3.v4",
	},
	shim: {
		"js/3rdparty/tinycolor": {
			"exports": 'tinycolor'
		},
        "js/3rdparty/ol": {
            "exports": "ol"
        },
        "js/3rdparty/d3": {
            "exports": "d3"
        },
	},
	packages: [
	    {name: 'js/map/controls', main: 'index'},
	    {name: 'js/forms', main: 'index'},
	    {name: 'js/apps', main: 'index'},
	    {name: 'js/ui', main: 'index'},
	    {name: 'js/vis', main: 'index'},
	]
});

initial_data = initial_data || {};
context = context || {};
context.timeOffset = context.timeOffset || 13;  // +8 for Asia/Shanghia and +5 for EST
context.initialFilter = context.initialFilter || {};
context.initialFilter.date = context.initialFilter.date || ['2011-12-01', '2011-12-30'];
console.log("Context: ", context)

require([
    "js/map/map",
    "js/vis",
    "js/apps/" + context.appType,
    "js/3rdparty/d3"
],
function(map, vis, app, d3) {

    function setup(map, vis, app, db, d3) {
        context.app = app;
        context.db = db;

        context.app.setup();

        console.log("Initial Data: ", initial_data);
        var dataObj = null;
        if( "getDataObj" in context.app ) {
            var dataObj = context.app.getDataObj();
            dataObj.load(null);
        }

        var map = new map.Map(dataObj, context, 'content');

        var countFormat1 = d3.format("d");
        var countFormat2 = d3.format(".1f");
        var countFormat3 = d3.format("d");
        var avgSpdFormat = d3.format("d");
        var details = document.getElementById("details");
        var chart = document.createElement("div");
        var controls = document.createElement("div");
        chart.id = "chart";
        controls.id = "chartControls";

        function getCounts(d) {
            var props = d.getProperties();
            var sum = 0;
            if( "cube" in props ) {
                sum = d.getProperties().cube.counts.reduce(function(a, b) {
                    return a + b;
                }, 0);
            }
            return sum;
        }

        function getAvgSpeed(d) {
            var sumSpeed = d.getProperties().cube.sums.reduce(function(a, b) {
                return a + b;
            }, 0);
            var count = getCounts(d);
            return sumSpeed / count;
        }

        var chartSelect = document.createElement('fieldset');
        var legend = document.createElement("legend");
        // legend.innerHTML = "Chart Data";
        chartSelect.appendChild(legend);
        controls.appendChild(chartSelect);
        details.appendChild(chart);
        details.appendChild(controls);
        this.dataTypes = {
            "Count": {
                key: function(d) {
                    return d.getId();
                },
                x: function(d) {
                    return d.getProperties().name;
                },
                y: getCounts,
                // width: getAvgSpeed,
                yName: "Count",
                xName: "Street",
                yFormat: function(d) {
                    if( d < 500 ) {
                        return countFormat3(d);
                    } else if ( d > 4000 ) {
                        return countFormat1(d/1000) + "K";
                    } else {
                        return countFormat2(d/1000) + "K";
                    }
                }
            },
            "Avg. Speed": {
                key: function(d) {
                    return d.getId();
                },
                x: function(d) {
                    return d.getProperties().name;
                },
                y: getAvgSpeed,
                // width: getCounts,
                yName: "Avg. Speed",
                xName: "Street",
                yFormat: function(d) {
                    return avgSpdFormat(d) + " km/h";
                }
            }
        };

        for( let prop in this.dataTypes ) {
            this.dataTypes[prop].element = "#chart";
            this.dataTypes[prop].margin = {
                top: 20,
                bottom: 50,
                left: 60,
                right: 20
            };
        }
        var bar = new vis.BarChart(this.dataTypes["Count"]);
        Object.keys(this.dataTypes).forEach(function(r, i) {
            var ctrl = document.createElement("input");
            ctrl.type = "radio";
            ctrl.name = "chartSelect";
            ctrl.value = r;
            ctrl.onchange = function(e) {
                bar.setOptions(self.dataTypes[r]);
                self.data.sort(function(a, b){
                    // Sorts descending
                    a = self.dataTypes[r].y(a);
                    b = self.dataTypes[r].y(b);
                    if( a < b ) return 1;
                    if( a > b ) return -1;
                    return 0;
                });
                bar.setData(self.data);
            }
            if( i == 0 ) { ctrl.checked = true; }
            else { ctrl.checked = false; }
            chartSelect.appendChild(ctrl);
            var label = r.charAt(0).toUpperCase() + r.slice(1).replace('_', ' ');
            chartSelect.appendChild(document.createTextNode(label + " "));
            if( i > 0 && (i%5) == 0 ) {
                chartSelect.appendChild(document.createElement("br"));
            }
        }, this);
        self.data = [];
        map.selector.on("select", function(e){
            var dataSelector = $(chartSelect).find("input");
            var valueFunction = null;
            for( let p = 0; p < dataSelector.length; p++ ) {
                var input = dataSelector[p];
                if( dataSelector[p].checked ) {
                    valueFunction = self.dataTypes[dataSelector[p].value].y;
                    break;
                }
            }
            // TODO: Seems like saving the data here shouldn't be required but d3 modifies the array
            self.data = e.target.selectedFeatures.getArray();
            if( valueFunction ) {
                self.data.sort(function(a, b){
                    // Sorts descending
                    a = valueFunction(a);
                    b = valueFunction(b);
                    if( a < b ) return 1;
                    if( a > b ) return -1;
                    return 0;
                });
            }
            bar.setData(self.data);
        });
    }

    const useLocalDb = false;
    const dbName = "cubesets";
    const dbVersion = 1;

    if( useLocalDb ) {
        var request = indexedDB.open(dbName, dbVersion);

        request.onerror = function(event) {
            console.error("Error creating local database.")
        };
        request.onupgradeneeded = function(event) {
            console.log("Upgrading local database");
            var db = event.target.result;
            var objectStore = db.createObjectStore("streets", { keyPath: "geo.id" });
            objectStore.createIndex("url", "url", { unique: false, multiEntry: true });
            objectStore.createIndex("region", "geo.properties.cubesets.region", { unique: false });
            objectStore.createIndex("category", "geo.properties.cubesets.category", { unique: false });

            var urlMapping = db.createObjectStore("urlMapping", { keyPath: "url" });
        };
        request.onsuccess = function(event) {
            console.log("Local database created/connected.");
            var db = event.target.result;
            setup(map, vis, app, db, d3);
        }
    } else {
        setup(map, vis, app, null, d3);
    }
});