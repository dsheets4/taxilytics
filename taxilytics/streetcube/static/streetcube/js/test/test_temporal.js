define([
    "streetcube/js/test/test_base",
    "streetcube/js/cube/temporal",
    "js/util"
],
function(TestCase, TemporalCube, util){

    function TemporalTestCase(cube) {
        TestCase.call(this);
        this.name = "Temporal Test";
        this.tests = {};
        this.timing = {};

        // To get better timing the function validates the query outside the formal test.
        // If the query is valid then the test simply performs the query.  Otherwise a
        // different test is returned to propagate the query failure reason.
        function createQueryTestFunction(query) {
            try {
                cube.validateQuery(query);
                return function() {
                    return cube.query(query);
                }
            } catch( e ) {
                return function() {
                    throw e;
                }
            }
        }

        var dateRange1 = [
            util.parseDateTime("2011-12-03T03:00:00+00:00"),
            util.parseDateTime("2011-12-03T04:00:00+00:00")
        ];
        var dateRange2 = [
            util.parseDateTime("2011-12-05T03:00:00+00:00"),
            util.parseDateTime("2011-12-06T04:00:00+00:00")
        ];
        var dateRange3 = [
            util.parseDateTime("2011-12-08T03:00:00+00:00"),
            util.parseDateTime("2011-12-10T04:00:00+00:00")
        ];
        var dateRangeOutOfPhase = [
            util.parseDateTime("2011-12-08T03:30:00+00:00"),
            util.parseDateTime("2011-12-10T04:15:00+00:00")
        ];
        var dateRangeDaily = [
            util.parseDateTime("2011-12-01T00:00:00+00:00"),
            util.parseDateTime("2011-12-07T00:00:00+00:00")
        ];
        var dateRangeWeekly = [
            util.parseDateTime("2011-12-01T00:00:00+00:00"),
            util.parseDateTime("2012-01-01T00:00:00+00:00")
        ];

        var entireRange = cube.extents();

        var entireRangeStartMidnight = cube.extents();
        entireRangeStartMidnight[0].setUTCHours(0);

        // Lookup a continuous time range
        this.timing["Single Continuous Range within 1 day"] = createQueryTestFunction({
            extents: [dateRange1]
        });

        this.timing["Single Continuous Range across 2 days"] = createQueryTestFunction({
            extents: [dateRange2]
        });

        this.timing["Single Continuous Range across 3 days"] = createQueryTestFunction({
            extents: [dateRange3]
        });

        this.timing["Continuous Range with out of phase extents"] = createQueryTestFunction({
            extents: [dateRangeOutOfPhase]
        });

        // Lookup multiple continuous time range
        this.timing["Multiple separate continuous ranges"] = createQueryTestFunction({
            extents: [
                dateRange1,
                dateRange2,
                dateRange3,
                dateRangeDaily,
                dateRangeWeekly
            ],
        });

        // Lookup multiple continuous time range
        this.timing["Daily cells, no groups"] = createQueryTestFunction({
            extents: [dateRangeDaily],
            indexer: new TemporalCube.indexers.Indexer({
                cell: 60 * 60 * 24
            })
        });

        // Lookup multiple continuous time range
        this.timing["Daily cells, no groups, 1 day interval"] = createQueryTestFunction({
            extents: [dateRangeDaily],
            indexer: new TemporalCube.indexers.Indexer({
                cell: 60 * 60 * 24,
                interval: 60 * 60 * 24
            })
        });

        // Lookup multiple continuous time range
        this.timing["Weekly cells, no groups"] = createQueryTestFunction({
            extents: [dateRangeWeekly],
            indexer: new TemporalCube.indexers.Indexer({
                cell: 60 * 60 * 24 * 7
            })
        });

        // Lookup multiple continuous time range
        this.timing["Hourly cells, Daily groups (chart)"] = createQueryTestFunction({
            extents: [entireRangeStartMidnight],
            indexer: new TemporalCube.indexers.HourOfDay()
        });

        // Lookup multiple continuous time range
        this.timing["Daily cells, Weekly groups (chart)"] = createQueryTestFunction({
            extents: [entireRangeStartMidnight],
            indexer: new TemporalCube.indexers.DayOfWeek()
        });

        // Lookup multiple continuous time range
        this.timing["Daily cells, no groups (summary chart)"] = createQueryTestFunction({
            extents: [entireRangeStartMidnight],
            indexer: new TemporalCube.indexers.Indexer({
                cell: 60 * 60 * 24,
            })
        });
    }

    TemporalTestCase.prototype = Object.create(TestCase.prototype);
    TemporalTestCase.prototype.constructor = TemporalTestCase;

    return TemporalTestCase;
});