define([
    "js/util",
    "streetcube/js/cube/cube_utils",
    "streetcube/js/cube/cube_base",
],
function(util, cube_utils, base) {

    function dayRecCmp(a, b) {
        a = a.id;
        b = b.id;
        if( a > b ) return 1;
        if( a < b ) return -1;
        return 0;
    }

    function getDayId(t) {
        return (t.getUTCFullYear() * 10000) + (t.getUTCMonth() * 100) + t.getUTCDate();
    }

    function ymdFromDayId(id) {
        id = "" + id;
        var y = parseInt(id.slice(0,4));
        var m = parseInt(id.slice(4,6));
        var d = parseInt(id.slice(6));
        return {y: y, m: m, d: d};
    }

    function weekNoFromDayId(id) {
        id = "" + id;
        var y = parseInt(id.slice(0,4));
        var m = parseInt(id.slice(4,6));
        var d = parseInt(id.slice(6));
        return util.weekNumber(new Date(y, m, d));
    }

    function getTodId(t) {
        return (t.getUTCHours() * 3600) + (t.getUTCMinutes() * 60) + t.getUTCSeconds();
    }


    // --------------------------------------
    function Indexer(fields) {
        fields = fields || {};
        if( typeof(fields.cell) !== "undefined" ) {
            // Input is in seconds but implementation uses ms.
            this._cell = fields.cell * 1000;
        }
        if( typeof(fields.group) !== "undefined" ) {
            this._group = fields.group;
        }
        if( typeof(fields.interval) !== "undefined" ) {
            // Input is in seconds but implementation uses ms.
            this._interval = fields.interval * 1000;
        }
        if( typeof(fields.anchor) !== "undefined" ) {
            // Input is Date object.
            this._anchor = fields.anchor.valueOf();
        } else {
            this._anchor = 0;
        }
    }
    Indexer.prototype = Object.create(null);
    Indexer.prototype.constructor = Indexer;

    Indexer.prototype.group = function() {
        return this._group;
    }

    Indexer.prototype.cell = function(date) {
        return this._cell;
    }

    Indexer.prototype.interval = function() {
        // TODO: Update interval to be an array defining a pattern of cellsToInclude, cellsToSkip
        //       Some examples: [5,2] -> Include 5 cells, skip 2.
        return this._interval;
    }

    Indexer.prototype.anchor = function() {
        return this._anchor;
    }

    Indexer.prototype.index = function(t, i) {
        var startTime = t.valueOf() - this._anchor;
        return parseInt((startTime % (this._group * this._cell)) / (this._cell));
    }

    Indexer.prototype.cellOffset = function(t) {
        var startTime = t.valueOf() - this._anchor;
        return this._cell - (startTime % (this._cell));
    }


    // --------------------------------------
    function HourlyIndexer(fields) {
        Indexer.call(this, fields);
        this._cell = 1000 * 60 * 60;
        this._group = undefined;
        this._anchor = 0;
    }
    HourlyIndexer.prototype = Object.create(Indexer.prototype);
    HourlyIndexer.prototype.constructor = HourlyIndexer;


    // --------------------------------------
    function HourOfDayIndexer(fields) {
        Indexer.call(this, fields);
        this._cell = 1000 * 60 * 60;
        this._group = 24;
        this._anchor = 0;
    }
    HourOfDayIndexer.prototype = Object.create(Indexer.prototype);
    HourOfDayIndexer.prototype.constructor = HourOfDayIndexer;


    // --------------------------------------
    function DayOfWeekIndexer(fields) {
        Indexer.call(this, fields);
        this._cell = 1000 * 60 * 60 * 24;
        this._group = 7;
        this._anchor = 1000 * 60 * 60 * 24 * 4;  // Epoch is Thurs, Jan 1, 1970
    }
    DayOfWeekIndexer.prototype = Object.create(Indexer.prototype);
    DayOfWeekIndexer.prototype.constructor = DayOfWeekIndexer;


    // --------------------------------------
    function WeekOfYearIndexer(fields) {
        Indexer.call(this, fields);
        // TODO: This requires a function to properly calculate the cells.
        this._cell = 1000 * 60 * 60 * 24 * 7;
        this._group = 12;
        this._anchor = 0;
    }
    WeekOfYearIndexer.prototype = Object.create(Indexer.prototype);
    WeekOfYearIndexer.prototype.constructor = WeekOfYearIndexer;


    // --------------------------------------
    function MonthOfYearIndexer(fields) {
        Indexer.call(this, fields);
        // TODO: This requires a function to properly calculate the cells.
        this._cell = 1000 * 60 * 60;
        this._group = 24;
        this._anchor = 0;
    }
    MonthOfYearIndexer.prototype = Object.create(Indexer.prototype);
    MonthOfYearIndexer.prototype.constructor = MonthOfYearIndexer;


    // --------------------------------------
    function TemporalCube(options) {
        base.Cube.call(this, options);
        this.temporal = {};
        this.days = [];
    }
    TemporalCube.prototype = Object.create(base.Cube.prototype);
    TemporalCube.prototype.constructor = TemporalCube;

    TemporalCube.indexers = {
        Indexer: Indexer,
        Hourly: HourlyIndexer,
        HourOfDay: HourOfDayIndexer,
        DayOfWeek: DayOfWeekIndexer,
    }

    TemporalCube.DefaultIndexer = new Indexer();

    TemporalCube.prototype.temporalExtents = function() {
        var start = this.days[0];
        var end = this.days[this.days.length-1];
        return [
            new Date(start.times[0].date),
            new Date(end.times[end.times.length-1].date)
        ]
    }

    var localTimezoneOffset = (new Date().getTimezoneOffset()) / 60;
    TemporalCube.prototype.mergeSet = function(set) {
        for( let s_id in set ) {
            var street = set[s_id];
            this.template = base.createMetricTemplate(street);
            this.templateStr = JSON.stringify(this.template);

            // TODO: Use an accessor function in TemporalCube to get times
            street.times.forEach(function(t, i){
                var t = util.parseDateTime(t);
                // TODO: Any processing of time such as the TZ offset should be provided via time accessor
                // TODO: The +8 offset is for China.  Replace with context as part of data or query.
                t.setUTCHours(t.getUTCHours()+localTimezoneOffset+8);
                street.times[i] = t;

                // Ensure the year entry exists.
                if( !(t.getUTCFullYear() in this.temporal) ) {
                    this.temporal[t.getUTCFullYear()] = {
                        months: {},
                        weeks: {}
                    };
                }
                var year = this.temporal[t.getUTCFullYear()];

                // Ensure the month entry exists.
                if( !(t.getUTCMonth() in year.months) ) {
                    year.months[t.getUTCMonth()] = [null, null];
                }

                // Ensure the week entry exists.
                var weekNo = util.weekNumber(t);
                if( !(weekNo in year.weeks) ) {
                    year.weeks[weekNo] = [null, null]
                }
                var tmpRec = {
                    id: getDayId(t),
                    data: JSON.parse(this.templateStr)
                }
                var dayRec = cube_utils.binarySearch(this.days, tmpRec, dayRecCmp);
                if( dayRec != null ) {
                    dayRec = this.days[dayRec];
                } else {
                    dayRec = tmpRec;
                    dayRec.times = [];
                    this.days.push(dayRec);
                    this.days = this.days.sort(dayRecCmp);
                }
                var todId = getTodId(t);
                tmpRec = JSON.parse(this.templateStr);
                tmpRec.id = todId;
                if( this.subCube.cubeType ) {
                    if( !(tmpRec.cube instanceof this.subCube.cubeType) ) {
                        tmpRec.cube = new this.subCube.cubeType(this.subCube.options);
                    }
                }
                var timeIdx = cube_utils.binarySearch(dayRec.times, tmpRec, dayRecCmp);
                if( timeIdx != null ) {
                    tmpRec = dayRec.times[timeIdx];
                } else {
                    tmpRec.date = new Date(t.valueOf());
                    dayRec.times.push(tmpRec);
                    dayRec.times = dayRec.times.sort(dayRecCmp);
                }
                var tmpRec2 = {};
                for( var prop in this.template ) {
                    tmpRec2[prop] = street[prop][i];
                }
                if( tmpRec.cube ) {
                    var obj = {};
                    obj[s_id] = tmpRec2;
                    tmpRec.cube.mergeSet(obj);
                }
                tmpRec = this.merge(tmpRec, tmpRec2);
            }, this);
        }

        // Final day by day processing.
        this.agg = JSON.parse(this.templateStr);
        for( let i = 0; i < this.days.length; i++ ) {
            var d = this.days[i];

            // Create the monthly index
            var ymd = ymdFromDayId(d.id);
            var m = this.temporal[ymd.y].months[ymd.m];
            if( m[0] == null || i < m[0] ) { m[0] = i; }
            if( m[1] == null || i > m[1] ) { m[1] = i; }

            // Create the weekly index
            var weekNo = weekNoFromDayId(d.id);
            var w = this.temporal[ymd.y].weeks[weekNo];
            if( w[0] == null || i < w[0] ) { w[0] = i; }
            if( w[1] == null || i > w[1] ) { w[1] = i; }

            // Create roll-up aggregation on the day
            for( let i = 0; i < d.times.length; i++ ) {
                var timeRec = d.times[i];
                if( d.times[i].cube ) {
                    d.times[i].agg = d.times[i].cube.getAggregate();
                }
                d.data = this.merge(d.data, d.times[i]);
            }

            // Create the overall roll-up aggregation
            this.agg = this.merge(this.agg, d.data);
        }
        this.agg.extents = this.temporalExtents();
    }

    TemporalCube.gValidateTimer = 0;
    TemporalCube.prototype.validateQuery = function(q) {
        var t0 = performance.now();
        if( q === null ) return; // Null query means return top-level aggregate.
        function isWholeNumber(n) {
            return !(isNaN(parseFloat(n)) && !(isFinite(n))) || ((n % 1) != 0)
        }

        if( !('extents' in q) ) {
            console.error("Query error:", q);
            throw "Query must define extents as absolute start and end times";
        }

        for( let prop in q ) {
            switch( prop ) {
                case 'extents':
                    if( typeof(q.extents) === "undefined" ) {
                        continue; // Undefined extents means return entire extents (i.e. aggregate)
                    }
                    // Defines the absolute time extents.
                    for( var i = 0; i < q.extents.length; i++ ) {
                        if( q.extents[i].length != 2 ) {
                            console.error("Query error:", q);
                            throw "Extents " + i + " must contain exactly two values ";
                        }
                        var start = q.extents[i][0];
                        var end = q.extents[i][1];
                        if( !(start instanceof Date) || !(end instanceof Date)) {
                            console.error("Query error:", q);
                            throw "Extents " + i + " must be instance of Date().";
                        }
                        if( end < start ) {
                            console.error("Query error:", q);
                            throw "Extents " + i + " start must be less than or equal to end.";
                        }
                    }
                    break;
                case 'indexer':
                    if( !(q.indexer instanceof Indexer) ) {
                        console.error("Query error:", q);
                        throw "Property 'indexer' must be of type Indexer.";
                    }
                    var cell = q.indexer.cell();
                    var group = q.indexer.group();
                    var interval = q.indexer.interval();
                    if( typeof(cell) !== "undefined" && !isWholeNumber(cell) ) {
                        console.error("Query error:", q);
                        throw "Indexer 'cell' must be in whole numbers of seconds.";
                    }
                    if( typeof(group) !== "undefined" && !isWholeNumber(group) ) {
                        console.error("Query error:", q);
                        throw "Indexer 'group' must be in whole numbers of seconds.";
                    }
                    if( typeof(interval) !== "undefined" && !isWholeNumber(interval) ) {
                        console.error("Query error:", q);
                        throw "Indexer 'interval' must be in whole numbers of seconds.";
                    }
                    break;
                case 'subQuery':
                    if( this.days.length > 0 && this.days[0].times.length > 0 ) {
                        this.days[0].times[0].cube.validateQuery(q.subQuery);
                    }
                    break;
                default:
                    console.error("Query error:", q);
                    throw "Unknown query value '" + prop + "'.";
            }

        }
        var t1 = performance.now();
        TemporalCube.gValidateTimer += (t1-t0);
        return true;
    }

    TemporalCube.gTimer = 0;
    TemporalCube.prototype.query = function(q, callback) {
        var t0 = performance.now();
        if( typeof(q.indexer) === "undefined" && (q == null || !(q.extents)) ) {
            return this.agg;
        }
        if( typeof(q.extents) === "undefined" ) {
            q.extents = [this.temporalExtents()];
        }
        var cells = q.extents;

        var indexer;
        if( typeof(q.indexer) !== "undefined" ) {
            indexer = q.indexer;
        } else {
            indexer = TemporalCube.DefaultIndexer
        }

        if( indexer.cell() ) {
            cells = [];
            // Expand the query parameters
            let startDate;
            let endDate;
            let localEndDate;
            for( let j=0; j < q.extents.length; j++ ) {
                var queryExtents = q.extents[j];
                startDate = queryExtents[0];
                endDate = queryExtents[1];
                while( startDate < endDate ) {
                    localEndDate = new Date(startDate.valueOf() + (indexer.cellOffset(startDate)));
                    if( localEndDate > endDate ) {
                        localEndDate = endDate;
                    }
                    cells.push([startDate, localEndDate]);
                    startDate = localEndDate;
                    if( indexer.interval() ) {
                        startDate = new Date(startDate.valueOf() + indexer.interval());
                    }
                }
            }
        }

        var results;
        if( indexer.group() ) {
            results = new Array(indexer.group());
        } else {
            results = [];
        }

        var singleResult;
        var cubeTotalExtents = this.temporalExtents();
        for( let j=0; j < cells.length; j++ ) {
            singleResult = JSON.parse(this.templateStr);
            var startDate = cells[j][0];
            var endDate = cells[j][1];

            // Narrow down to a possible range of indices based on data structure.
            var startIdx, endIdx;
            try {
                startIdx = this.temporal[startDate.getUTCFullYear()].months[startDate.getUTCMonth()];
            } catch(e) {
                startIdx = undefined;
            }
            if( typeof(startIdx) === "undefined" ) {
                startIdx = [0, this.days.length-1];
            }
            if( endDate > cubeTotalExtents[1] ) {
                if( startDate > cubeTotalExtents[1] ) {
                    continue;  // There are no results.
                } else {
                    endIdx = undefined;
                }
            } else {
                try {
                    endIdx = this.temporal[endDate.getUTCFullYear()].months[endDate.getUTCMonth()];
                } catch(e) {
                    endIdx = undefined;
                }
            }
            if( typeof(endIdx) === "undefined" ) {
                endIdx = [startIdx[0], this.days.length - 1]
            }

            // Search possible range of indices for exact start, end points.
            startIdx = cube_utils.binarySearch(
                this.days,
                {id: getDayId(startDate)},
                dayRecCmp,
                {min: startIdx[0], max: startIdx[1], approx: "upper"}
            );
            endIdx = cube_utils.binarySearch(
                this.days,
                {id: getDayId(endDate)},
                dayRecCmp,
                {min: endIdx[0], max: endIdx[1], approx: "lower"}
            );

            var streets;
            var s

            // Get partial sum from the first day.
            var dayRec = this.days[startIdx];
            var startTimeIdx = cube_utils.binarySearch(
                dayRec.times,
                {id: getTodId(startDate)},
                dayRecCmp,
                { approx: "upper" }
            );
            if( startTimeIdx != null ) {
                var endTimeIdx;
                if( startIdx == endIdx ) {
                    endTimeIdx = cube_utils.binarySearch(
                        dayRec.times,
                        {id: getTodId(endDate)},
                        dayRecCmp,
                        { min: startTimeIdx, approx: "lower" }
                    );
                } else {
                    endTimeIdx = dayRec.times.length - 1;
                }
                for( let i = startTimeIdx; i <= endTimeIdx; i++ ) {
                    this.merge(singleResult, dayRec.times[i]);
                    // dayRec.times[i] contains the StreetCube
                    // streets = this.subCube.mergeResult(streets, );
                }
            }

            // Gather sums from included whole days.
            for( let i = startIdx+1; i < endIdx; i++ ) {
                dayRec = this.days[i];
                this.merge(singleResult, dayRec.data)
            }

            // Get partial sum from last day.
            if( startIdx != endIdx && endIdx != null ) {
                dayRec = this.days[endIdx];
                endTimeIdx = cube_utils.binarySearch(
                    dayRec.times,
                    {id: getTodId(endDate)},
                    dayRecCmp,
                    {approx: "lower"}
                );
                if( endTimeIdx != null ) {
                    for( var i = endTimeIdx; i >= 0; i-- ) {
                        this.merge(singleResult, dayRec.times[i]);
                    }
                }
            }

            if( indexer.group() ) {
                var idx = indexer.index(startDate, j);
                if( !results[idx] ) {
                    singleResult.toString = function() {
                        return " Avg=" + (this.sums / this.counts).toFixed(3);
                    }
                    singleResult.extents = [idx,idx+1];
                    results[idx] = singleResult;
                } else {
                    this.merge(results[idx], singleResult);
                }
            } else {
                singleResult.toString = function() {
                    return " Avg=" + (this.sums / this.counts).toFixed(3);
                }
                singleResult.extents = [startDate, endDate];
                results.push(singleResult);
            }
        }
        for( let i=0; i<results.length; i++ ) {
            if( !results[i] ) {
                results[i] = JSON.parse(this.templateStr);
                results[i].extents = [null,null];
            }
        }
        var t1 = performance.now();
        TemporalCube.gTimer += (t1 - t0);
        return results;
    }

    var compareExtents = function(l, r) {
        if( l[0] instanceof Date ) {
            if( l[0].getTime() == r[0].getTime() &&
                l[1].getTime() == r[1].getTime() ) {
                return true;
            }
        } else {
            if( l[0] == r[0] && l[1] == r[1] ) {
                return true;
            }
        }
        return false;
    }

    TemporalCube.prototype.mergeResult = function(target, input) {
        if( !target ) {
            target = [];
        }
        var j = 0;
        for( let i=0; i<input.length; i++ ) {
            if( j < target.length ) {
                if( !compareExtents(target[j].extents, input[i].extents) ) {
                    console.error("Mismatched extents needs implemented", j, i, target[j].extents, input[i].extents)
                }
            }
            target[i] = this.merge(target[j], input[i]);
            j++;
        }
        return target;
    }

    return TemporalCube;
});
