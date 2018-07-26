requirejs.config({
	// By default load any module IDs from static/js
	// TODO: Static is a hardcoded variable that should come from server framework
	baseUrl : '/static',

	// paths: When a request for the key comes in, look in value instead.
	paths: {
	    "js/3rdparty/d3": "js/3rdparty/d3.v4.min",
	},
	shim: {
        "js/3rdparty/d3": {
            "exports": "d3"
        },
	},
	packages: [
	    {name: 'js/vis', main: 'index'},
	    {name: 'streetcube/js/cube', main: 'index'},
	    {name: 'streetcube/js/test', main: 'index'},
	]
});

require([
    "streetcube/js/test-view",
    "streetcube/js/stackcube",
    "streetcube/js/test",
    "js/util"
],
function(view, stackcube, test, util) {
    // Calling jQuery with a function like this runs the function once the page is loaded.
    $(function run() {
        view.setStatus("Downloading available cubesets");

        stackcube.getAvailableSets(function(cubeSets) {
            console.log("Available cube sets:", cubeSets);
            view.setStatus("Preparing to download cube sets.");

            function runTests(cube) {
                [
                    new test.TemporalTestCase(cube),
                    new test.UtilTestCase(creationTime),
                ].forEach(function testRunAndTime(t) {
                    timing.setStatus("Starting Test: " + t.name);
                    var results = t.run();
                    timing.addResults(t, results);
                });
                timing.setStatus("Timing and Tests Complete!");
            }

            var cubeRequestRef = cubeSets.regions.system.features;
            timing.setStatus("Requesting cube set data:", cubeRequestRef);
            var creationTime = null;
            var timer = new util.Timer("Cube creation");
            cube.requestCubeSet(cubeRequestRef, {
                done: function(cube) {
                    creationTime = timer.stop(true);
                    console.log("Created cube:", cube);
                    runTests(cube);
                },
                setLoaded: function(data, loaded, total) {
                    timing.setStatus("Loaded " + loaded + " of " + total + " sets.");
                }
            });
        });
    });
});