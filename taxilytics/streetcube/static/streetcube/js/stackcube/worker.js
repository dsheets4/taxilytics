
onmessage = function(e) {
    var t0 = performance.now();
    var cube = e.data[0];
    var query = e.data[1];
    var result = e.data[2];
    var subResult = cube.query(query);
    var t1 = performance.now();
    postMessage(
        subResult,  // Data results from the query
        cube,       // Cube that was queried
        result,     // Current aggregated results
        (t1-t0)     // Performance timing for the operation (milliseconds)
    );
}