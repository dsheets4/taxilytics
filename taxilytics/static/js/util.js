define([], function(){
    var util = {};

    // ************************************************************************
    // From: https://stackoverflow.com/a/19807441
    util.getScriptName = function getScriptName() {
        var error = new Error()
          , source
          , lastStackFrameRegex = new RegExp(/.+\/(.*?):\d+(:\d+)*$/)
          , currentStackFrameRegex = new RegExp(/getScriptName \(.+\/(.*):\d+:\d+\)/);

        if((source = lastStackFrameRegex.exec(error.stack.trim())) && source[1] != "")
            return source[1];
        else if((source = currentStackFrameRegex.exec(error.stack.trim())))
            return source[1];
        else if(error.fileName != undefined)
            return error.fileName;
    }

    // ************************************************************************
    util.parseDateTime = function(str, timeOffset) {
        if( typeof(timeOffset) === "undefined" ) {
            if( typeof(context) !== "undefined" && typeof(context.timeOffset) !== "undefined" ) {
                timeOffset = context.timeOffset;
            } else {
                timeOffset = 0;
            }
        }
        if( str instanceof Date ) { return str; }
        var m = str.match(/^(\d{4})-(\d{2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d{1,2})\+00:00$/);
        var offset = (m) ? Date.UTC(m[1], m[2]-1, m[3], m[4], m[5], m[6]) : null;
        if( offset ) {
            offset += timeOffset * 60 * 60 * 1000;
            return new Date(offset);
        }
        return null;
    }

    util.weekNumber = function(d){
        d = new Date(+d);
        d.setUTCHours(0,0,0,0);
        d.setDate(d.getUTCDate()+4-(d.getUTCDay()||7));
        return Math.ceil((((d-new Date(d.getUTCFullYear(),0,1))/8.64e7)+1)/7);
    };

    function zeroPad(num, places) {
        var zero = places - num.toString().length + 1;
        return Array(+(zero > 0 && zero)).join("0") + num;
    }


    // ************************************************************************
    util.parseHrefParams = function(href) {
        var pageParams = {};

        href = href || window.location.href, start, end, paramsString, pairs;

        if (href.indexOf('?') > 0) {
            start = href.indexOf('?') + 1;
            end = href.indexOf('#') > 0 ? href.indexOf('#') : href.length;
            paramsString = href.substring(start, end);
            pairs = paramsString.split(/[&;]/);
            for (var i = 0; i < pairs.length; ++i) {
                pair = pairs[i].split('=');
                if (pair[0]) {
                    var val = decodeURIComponent(pair[1]);
                    if     ( val === "true" ) val = true;
                    else if( val === "false") val = false;
                    pageParams[decodeURIComponent(pair[0])] = val;
                }
            }
        }
        return pageParams;
    }

    util.getCookie = function(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }


    // ************************************************************************
    // EventObject
    util.EventObject = function EventObject() {
        this.callbacks = [];
    }

    util.EventObject.prototype.addListener = function(callback, thisObj, extraArgs) {
        this.callbacks.push({
            callback: callback,
            thisObj: thisObj,
            extraArgs: extraArgs || [],
        });
    };

    util.EventObject.prototype.removeListener = function(callback, thisObj) {
        for (var i=(this.callbacks.length-1); i >= 0; i--) {
            if (callback == this.callbacks[i].callback && thisObj == this.callbacks[i].thisObj) {
                this.callbacks.splice(i, 1);
                break;  // Currently there's no prevention of multiple registers.
            }
        }
    }

    util.EventObject.prototype.emit = function(args) {
        if( !(args instanceof Array) ) {
            args = [args];
        }
        this.callbacks.forEach(function EventObject_emitOne(c) {
            c.callback.apply(c.thisObj, (args) ? args.concat(c.extraArgs) : c.extraArgs);
        });
    }


    // ************************************************************************
    // Emitter - An object that emits events
    util.Emitter = function Emitter() {
        this.events = {};
    }

    util.Emitter.prototype.on = function(evtName, callback, thisObj, extraArgs) {
        if( evtName in this.events ) {
            this.events[evtName].addListener(callback, thisObj, extraArgs);
        } else {
            console.error("Event " + name + " does not exist on object.");
        }
        return this;
    }

    util.Emitter.prototype.remove = function(evtName, callback, thisObj) {
        if( evtName in this.events ) {
            this.events[evtName].removeListener(callback, thisObj);
        }
        return this;
    }

    util.Emitter.prototype.emit = function(evtName, args) {
        if( evtName in this.events ) {
            this.events[evtName].emit(args);
        }
    }

    // ************************************************************************
    // Emitter - An object that emits events
    util.Timer = function Timer(name) {
        this.name = name;
        this.start = window.performance.now();
    }

    util.Timer.prototype.stop = function(print) {
        var duration_ms = window.performance.now() - this.start;
        if( typeof(print) !== "undefined" && print ) {
            console.log(this.name + ": " + duration_ms + "ms");
        }
        return duration_ms;
    }

    util.Timer.prototype.reset = function() {
        this.start = window.performance.now();
    }

    return util;
});