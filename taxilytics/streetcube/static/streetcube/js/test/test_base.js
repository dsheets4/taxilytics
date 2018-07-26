define([
    "js/util",
],
function(util) {
    // Create a new object, that prototypically inherits from the Error constructor
    function TestFail(message) {
        this.name = 'TestFail';
        this.message = message || 'Default Message';
        this.stack = (new Error()).stack;
    }
    TestFail.prototype = Object.create(Error.prototype);
    TestFail.prototype.constructor = TestFail;

    function TestCase() {
    }

    TestCase.prototype.run = function (callbacks) {
        if( typeof(callbacks) === "undefined" ) {
            callbacks = {};
        }
        var timer = null;
        var results = {
            individuals: {},
            cumulative: {
                tests: 0,
                success: 0,
                fail: 0,
                error: 0
            }
        }
        var timePrecision = 6;
        function runSingle(testName, test) {
            var results = {};
            console.log("Starting test " + testName);
            timer = new util.Timer(this.name + ": " + testName);
            try {
                results.returnValue = test.call(this);
                results.time = timer.stop();
                if( typeof(results.returnValue) === "undefined" || results.returnValue ) {
                    results.status = "success";
                } else {
                    results.status = "fail";
                }
                if( typeof(results.returnValue) === "undefined" ) {
                    results.returnValue = "";
                }
            } catch(e) {
                results.time = timer.stop();
                results.returnValue = e;
                results.status = "error";
                console.log(e);
            }
            return results;
        }
        for( let test in this.tests ) {
            if( typeof(callbacks.start) !== "undefined" ) {
                callbacks.start(test);
            }

            results.cumulative.tests++;
            var result = runSingle.call(this, test, this.tests[test]);
            results.individuals[test] = result;
            results.cumulative[result.status]++;
            results.cumulative.tests++;

            if( typeof(callbacks.end) !== "undefined" ) {
                callbacks.end(results.individuals[test]);
            }
        }

        var numTimes = 10;
        for( let test in this.timing ) {
            var sumTimes = 0, min, max;
            var result = null;
            var i = 0;
            if( typeof(callbacks.start) !== "undefined" ) {
                callbacks.start(test);
            }
            for( var i = 0; i < numTimes; ++i ) {
                result = runSingle.call(this, test, this.timing[test]);
                result.numExecutions++;
                results.individuals[test] = result;
                if( result.status !== "success" ) {
                console.log("Fail")
                    break;
                } else {
                    sumTimes += result.time;
                    min = (min ? Math.min(result.time, min) : result.time);
                    max = (max ? Math.max(result.time, max) : result.time);
                }
            }
            result.time = sumTimes / i;
            result.timeMin = min;
            result.timeMax = max;
            result.numExecutions = i;
            results.individuals[test] = result;
            results.cumulative[result.status]++;
            results.cumulative.tests++;
            if( typeof(callbacks.end) !== "undefined" ) {
                callbacks.end(result);
            }
        }

        return results;
    }

    TestCase.prototype.verify = function verify(l, r, message) {
        if( l != r ) {
            if( typeof(message) === "undefined" ) {
                message = "" + l + " != " + r;
            }
            throw new Error(message);
        }
    }

    return TestCase;
});