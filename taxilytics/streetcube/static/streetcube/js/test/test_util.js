define([
    "streetcube/js/cube/cube_utils",
    "streetcube/js/test/test_base",
],
function(cube_utils, TestCase){

    function wait(ms){
        var now = new Date().getTime();
        var end = now + ms;
        while(now < end) {
            now = new Date().getTime();
        }
    }

    function UtilTestCase(creationTime) {
        TestCase.call(this);
        this.name = "Utilities";

        this.tests = {};

        // Verify that binary search works as expected.
        this.tests["Multiple Binary Search Functions"] = function() {
            var data = [];
            var idx = null;
            var now1 = new Date(Date.now());

            // Test case for empty list.
            idx = cube_utils.binarySearch(data, now1, cube_utils.compare);
            this.verify(idx, null);

            // Test case for single item list.
            data.push(now1);
            idx = cube_utils.binarySearch(data, now1, cube_utils.compare);
            this.verify(idx, 0);

            // Test case for item not found.
            var now2 = new Date(now1.valueOf() - 10000);
            idx = cube_utils.binarySearch(data, now2, cube_utils.compare);
            this.verify(idx, null);

            // Test case with two items.
            data.push(now2);
            data.sort(cube_utils.compare);
            idx = cube_utils.binarySearch(data, now2, cube_utils.compare);
            this.verify(idx, 0);
            idx = cube_utils.binarySearch(data, now1, cube_utils.compare);
            this.verify(idx, 1);
        };

        this.tests["Binary Search Approx"] = function() {
            var arr = [];
            var idx;

            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare);
            this.verify(idx, null);
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare, {approx: "lower"});
            this.verify(idx, null);
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare, {approx: "upper"});
            this.verify(idx, null);

            arr = [0, 1, 2];
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare);
            this.verify(idx, null);
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare, {approx: "lower"});
            this.verify(idx, 2);
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare, {approx: "upper"});
            this.verify(idx, null);

            arr = [4, 5, 6];
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare);
            this.verify(idx, null);
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare, {approx: "lower"});
            this.verify(idx, null);
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare, {approx: "upper"});
            this.verify(idx, 0);

            arr = [0, 1, 2, 4, 5, 6];
            // Approximation results - Finding the closest record to a given bound.
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare);
            this.verify(idx, null);
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare, {approx: "lower"});
            this.verify(idx, 2);
            var idx = cube_utils.binarySearch(arr, 3, cube_utils.compare, {approx: "upper"});
            this.verify(idx, 3);

            // Predefined limits on the search.
            var idx = cube_utils.binarySearch(arr, 1, cube_utils.compare, {min: 2});
            this.verify(idx, null);
            var idx = cube_utils.binarySearch(arr, 5, cube_utils.compare, {max: 3});
            this.verify(idx, null);
            var idx = cube_utils.binarySearch(arr, 1, cube_utils.compare, {min: 1, max: 1});
            this.verify(idx, 1);
            var idx = cube_utils.binarySearch(arr, 5, cube_utils.compare, {min: 4, max: 4});
            this.verify(idx, 4);
        }

        var obj = {
             0: { speed: 0, count: 0 },
             1: { speed: 0, count: 1 },
             2: { speed: 0, count: 2 },
             3: { speed: 0, count: 3 },
             4: { speed: 0, count: 4 },
             5: { speed: 0, count: 5 },
             6: { speed: 0, count: 6 },
             7: { speed: 0, count: 7 },
             8: { speed: 0, count: 8 },
             9: { speed: 0, count: 9 },
            10: { speed: 0, count: 10 },
            11: { speed: 0, count: 11 },
            12: { speed: 0, count: 12 },
            13: { speed: 0, count: 13 },
            14: { speed: 0, count: 14 },
            15: { speed: 0, count: 15 },
            16: { speed: 0, count: 16 },
            17: { speed: 0, count: 17 },
            18: { speed: 0, count: 18 },
            19: { speed: 0, count: 19 },
            20: { speed: 0, count: 20 },
            21: { speed: 0, count: 21 },
            22: { speed: 0, count: 22 },
            23: { speed: 0, count: 23 },
        };
        this.tests["Object Lookup Time"] = function() {
            obj[0];
            obj[1];
            obj[2];
            obj[3];
            obj[4];
            obj[5];
            obj[6];
            obj[7];
            obj[8];
            obj[9];
            obj[10];
            obj[11];
            obj[12];
            obj[13];
            obj[14];
            obj[15];
            obj[16];
            obj[17];
            obj[18];
            obj[19];
            obj[20];
            obj[21];
            obj[22];
            obj[23];
        }

        var arr = [];
        for( let d in obj ) {
            arr.push(obj[d]);
        }
        this.tests["Array Lookup Time"] = function() {
            arr[cube_utils.binarySearch(arr, 0, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 1, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 2, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 3, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 4, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 5, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 6, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 7, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 8, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 9, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 10, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 11, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 12, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 13, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 14, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 15, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 16, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 17, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 18, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 19, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 20, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 21, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 22, cube_utils.compare)];
            arr[cube_utils.binarySearch(arr, 23, cube_utils.compare)];
        }

        this.tests["Cube Creation"] = function() {
            return creationTime.toFixed(6) + "ms";
        }

        var waitMs = 30;
        this.tests["Timer Wait " + waitMs + "ms"] = function() {
            wait(waitMs);
        }
    }

    UtilTestCase.prototype = Object.create(TestCase.prototype);
    UtilTestCase.prototype.constructor = UtilTestCase;

    return UtilTestCase;
});