define(["js/util"], function(util) {
    var data = {};
    var pagelimit = 1;

    // Retrieves data directly from the REST API.
    data.Base = function(opt_options) {

        util.Emitter.call(this);
        this.events = {
            "start": new util.EventObject(),
            "data": new util.EventObject(),
            "complete": new util.EventObject(),
            "cancel": new util.EventObject(),
        }

        var options = opt_options || {};
        this.collectPages = options.collectPages;
        if( typeof(this.collectPages) === "undefined" ) {
            this.collectPages = true;
        }
        this.storage = opt_options.storage || localStorage;

        this._loadOperations = 0;
        this.cancel = false;

        this.collectedPages = null;

        var self = this;

        this._setDataHandler = function(data, textStatus, jqXHR) {
            self.setData(data, this.url);
        }

        this.handleData = function(d, url, next) {
            if( self.collectPages === true ) {
                if( !self.collectedPages ) {
                    self.collectedPages = d;
                } else {
                    self.collectedPages.features = self.collectedPages.features.concat(d.features);
                }
            }
            else {
                self.emit("data", [d, self.layer]);
            }
        }

        this.dataComplete = function() {
            self.emit("data", [this.collectedPages, self.layer]);
            this.collectedPages = null;
        }

        this.decrementLoad = function() {
            if( this._loadOperations > 0 ) {
                this._loadOperations--;
            }
        }
    }

    data.Base.prototype = Object.create(util.Emitter.prototype);
    data.Base.prototype.constructor = data.Base;

    data.Base.prototype.cancelOperation = function(){
        this.cancel = true;
    };

    data.Base.prototype.requestNext = function(url) {
        this._loadOperations++;
        $.getJSON(url, this._setDataHandler);
    }

    data.Base.prototype.setData = function (data, url) {
        //console.log("setData", data)

        // Start of data loading.
        if(this._loadOperations === 0) {
            this.emit("start");
            this.collectedPages = null;
            this.cancel = false;
        }

        if( data ) {
            if( data.next && !this.cancel ){
                if( Array.isArray(data.next) ) {
                    data.next.forEach(this.requestNext, this);
                } else {
                    this.requestNext(data.next);
                }
            }

            // Handle current data page
            if( Array.isArray(data.results) ) {
                this.handleData(data.results, url, data.next);
                this.decrementLoad();
            }
            else {
                if( data.results ) {
                    this.handleData(data.results, url, data.next);
                    this.decrementLoad();
                }
                else if( !data.next ) {
                    this.handleData(data, url);
                    this.decrementLoad();
                }
            }
        }

        // Handle data completion, i.e. no more data to download.
        if( this._loadOperations === 0 ) {
            if( this.collectPages ) {
                this.dataComplete();
            }
            this.emit("complete", this.collectedPages);
        }
    };


    // Continues to access data using the next page feature.
    data.Rest = function(opt_options) {
        data.Base.call(this, opt_options);
    }
    data.Rest.prototype = Object.create(data.Base.prototype);
    data.Rest.prototype.constructor = data.Rest;

    data.Rest.prototype.load = function(d) {
        this.setData(d);
    }


    // Used with the cube data, which downloads everything and stores it locally.
    data.Cube = function(opt_options) {
        console.log("Cube Data Object options:", opt_options);
        data.Base.call(this, opt_options);
        opt_options = opt_options || {};

        this.osm = {};
        this.layer = opt_options.streetLayer;
        this.storage = opt_options.storage || null;

        var self = this;
        this.totalCount = 0;

        this.handleData = function(data, url, next) {
            if( typeof(url) !== "undefined" && this.storage != null ) {
                // Get a handle to the object store containing the cube sets.
                var objectStore = this.storage
                    .transaction("streets", "readwrite")
                    .objectStore("streets");
                // For each cube set in the returned data...
                for(var id in data) {
                    var datum = data[id];
                    // Check whether the cube set already exists.
                    var getRequest = objectStore.get(datum.geo.id);
                    getRequest.onsuccess = (function createAddHandler(datum) {
                        return function(event) {
                            var d = event.target.result;
                            var message = null;
                            if( typeof(event.target.result) === "undefined" ) {
                                // We're adding a new object.
                                datum.url = [url];
                                message = "Added new object";
                            } else {
                                // We're updating an existing object, maybe
                                datum = event.target.result;
                                var hasUrl = datum.url.find(function(u) {
                                    return u == url;
                                });
                                if( typeof(hasUrl) === "undefined" ) {
                                    datum.url.push(url);
                                    message = "Updated object";
                                }
                            }
                            if( message ) {
                                var putRequest = objectStore.put(datum);
                                putRequest.onsuccess = function(e) {
                                    // console.log(message, datum.geo.id, datum);
                                };
                                putRequest.onerror = function(e) {
                                    console.log("Error saving record id:", e);
                                }
                            }
                        }
                    })(datum)
                }

                if( next ) {
                    // Store the url -> next mapping to support multiple pages.
                    var urlMapping = this.storage
                        .transaction("urlMapping", "readwrite")
                        .objectStore("urlMapping");
                    var urlMap = {
                        url: url,
                        next: next
                    };
                    var urlRequest = urlMapping.put(urlMap);
                    urlRequest.onsuccess = function(e) {
                        // console.log(message, datum.geo.id, datum);
                    };
                    urlRequest.onerror = function(e) {
                        console.log("Error saving url mapping", urlMap);
                    }
                }
            }

            if( self.collectedPages == null ) {
                self.collectedPages = {
                    type: "FeatureCollection",
                    features: [],
                    crs: {
                        type: "name",
                        properties: {
                            name: "EPSG:3857"
                        }
                    },
                };
            }
            function merge(d) {
                context.app.collectionBuilder(d);
                if( typeof(self.cube) === "undefined" ) {
                    self.cube = {};
                }
                for( let osm in d ) {
                    if( !(osm in self.cube) ) {
                        self.cube[osm] = d[osm];

                        var street = self.cube[osm].geo;
                        street.properties.cube = self.cube[street.id];
                        if( !("info" in street.properties) ) {
                            street.properties.info = {};
                        }
                        street.properties.info.type = "cube";

                        self.collectedPages.features.push(street);
                    }
                    //else {
                    //    // console.log("Existing: ", self.cube[osm]);
                    //    // console.log("New     : ", d[osm]);
                    //    // console.error("Duplicate cube data!");
                    //}
                }
            }

            if( Array.isArray(data) ) {
                data.forEach(merge);
            }
            else {
                merge(data);
            }
            if( !self.collectPages ) {
                self.dataComplete()
            }
        }

        var self = this;
        this.dataComplete = function() {
            if( self.collectedPages ) {
                // TODO: Identify a way to remove street layer from data.js
                self.emit("data", [self.collectedPages, self.layer]);
                self.collectedPages = null;
            }
        }
    }
    data.Cube.prototype = Object.create(data.Base.prototype);
    data.Cube.prototype.constructor = data.Cube;

    data.Cube.prototype.requestNext = function(url) {
        var self = this;

        var serverRequest = function(url) {
            var parentProto = Object.getPrototypeOf(data.Cube.prototype);
            parentProto.requestNext.call(self, url);
            console.log("Loading from server.");
        }

        if( this.storage != null ) {
            var objectStore = this.storage
                .transaction("streets", "readwrite")
                .objectStore("streets");
            var cache = {
                next: null,
                results: {}
            }
            var urlIndex = objectStore.index("url");
            urlIndex.openCursor(IDBKeyRange.only(url)).onsuccess = function (event) {
                var cursor = event.target.result;
                if( cursor ) {
                    cache.results[cursor.value.geo.id] = cursor.value;
                    cursor.continue();
                }
                else {
                    if( Object.keys(cache.results).length > 0 ) {
                        // Local results ready to be loaded.
                        self.setData(cache);
                        // Setup second request for additional pages if they exist.
                        var objectStore = self.storage
                            .transaction("urlMapping")
                            .objectStore("urlMapping");
                        var getRequest = objectStore.get(url);
                        getRequest.onsuccess = function(event) {
                            var mapping = event.target.result;
                            self.setData(mapping);
                        }
                    } else {
                        // No results from local database, request from server.
                        serverRequest(url);
                    }
                }
            }
        } else {
            serverRequest(url);
        }
    }

    data.Cube.prototype.load = function(d) {
        this.setData(d);
    }

    return data;
});