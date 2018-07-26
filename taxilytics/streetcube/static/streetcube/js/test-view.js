define([
    "js/ui/datetimerange",
    "js/vis",
    "streetcube/js/cube/temporal"
],
function(DateTimeRangeSlider, vis, TemporalCube) {
    var timing = {};

    function nameToId(name) {
        var id = name.replace(' ', '_');
        return id;
    }

    timing.setStatus = function set_status(status) {
        console.log(status);//, "(set from " + set_status.caller.name + ")");
        $('#status').html(status);
    }

    timing.addResults = function add_results(testCase, results) {
        var form = $("#results");
        var id = nameToId(testCase.name);
        var myForm = form.append('<tr id="' + id + '" ><th class="main-header">' + testCase.name + '</th></tr>');
        var myResults = myForm.find('#' + id);
        var table = myResults.append("<table></table>");
        table.append("<tr><th>Test</th><th>Status</th><th>Return</th><th>Exe Time (ms)</th><th>Min Time (ms)</th><th>Max Time (ms)</th></tr>");
        for( let test in results.individuals ) {
            var result = results.individuals[test];
            var resultClass = 'class="' + result.status + '"';
            table.append("<tr " + resultClass + ">" +
                "<td>" + test + "</td>" +
                "<td>" + result.status + "</td>" +
                "<td>" + result.returnValue + "</td>" +
                "<td>" + result.time.toFixed(3) + "</td>" +
                "<td>" + (result.timeMin ? result.timeMin.toFixed(3) : "") + "</td>" +
                "<td>" + (result.timeMax ? result.timeMax.toFixed(3) : "") + "</td>" +
                "</tr>"
            );
        }
    }

    return timing;
});