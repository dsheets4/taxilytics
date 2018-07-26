define([], function() {
    const timeScale = 1000 * 60 * 60;  // ms/sec * sec/min * min/hr
    const sliderSelector = "#slider-range";

    DateTimeRangeSlider = function(parentElem, initial_range, opts) {
        var opts = opts || {};
        this.timeFmt = opts.timeFmt || function(t) {
            return t.toISOString();
        }
        this.onchange = opts.onchange || function(){};
        var self = this;

        this.ctrl = $('<div id="time-range">Start: <span class="slider-time"></span><div class="sliders_step1"><div id="slider-range"></div></div>End: <span class="slider-time2"></span></div>');
        this.ctrl.appendTo(parentElem);

        function uiToDate(ui) {
            return [
                new Date(ui.values[0]*timeScale),
                new Date(ui.values[1]*timeScale)
            ];
        }

        this.ctrl.find(sliderSelector).slider({
            range: true,
            step: 1,  // Increments in hours
            slide: function (e, ui) {
                var range = uiToDate(ui);
                self.selected(range);
                self.onchange(range);
            },
            change: function (e, ui) {
                var range = uiToDate(ui);
                self.onchange(range);
            }
        });
        this.extents(initial_range);
        this.selected(initial_range);
    };

    DateTimeRangeSlider.prototype = Object.create(null);
    DateTimeRangeSlider.prototype.constructor = DateTimeRangeSlider;

    DateTimeRangeSlider.prototype.extents = function(extents) {
        if( typeof(extents) === "undefined" ) {
            return [
                new Date(this.ctrl.find(sliderSelector).slider("option", "min")*timeScale),
                new Date(this.ctrl.find(sliderSelector).slider("option", "max")*timeScale)
            ];
        } else {
            // Date keeps time in ms.  We want times clamped to the nearest hour.
            this.ctrl.find(sliderSelector).slider("option", "min", extents[0] ? extents[0].valueOf()/timeScale : 0);
            this.ctrl.find(sliderSelector).slider("option", "max", extents[1] ? extents[1].valueOf()/timeScale : 0);
        }
    }

    DateTimeRangeSlider.prototype.selected = function(extents) {
        if( typeof(extents) === "undefined" ) {
            var extents = this.ctrl.find(sliderSelector).slider("option", "values");
            return [
                new Date(extents[0]*timeScale),
                new Date(extents[1]*timeScale)
            ];
        } else {
            this.ctrl.find('.slider-time').html(extents[0] ? this.timeFmt(extents[0]) : "null");
            this.ctrl.find('.slider-time2').html(extents[1] ? this.timeFmt(extents[1]) : "null");
            this.ctrl.find(sliderSelector).slider("values", [
                extents[0] ? extents[0].valueOf()/timeScale : 0,
                extents[1] ? extents[1].valueOf()/timeScale : 0
            ]);
        }
    }

    return DateTimeRangeSlider;
});