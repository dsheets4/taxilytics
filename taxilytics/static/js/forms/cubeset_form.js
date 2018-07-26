define(["js/3rdparty/ol"],
function(ol) {
    var CubesetForm = function(callbacks, opt_options) {
        this.options = opt_options | {};
        this.callbacks = callbacks;
        this.QueryRegionCommand = "QueryRegionSet";

        // Event handlers
        var self = this;

        this.form = document.createElement("div");
        this.form.innerHTML = "Loading cube sets."
    };

    function cleanLabel(s) {
        return s.charAt(0).toUpperCase() + s.slice(1).replace('_', ' ');
    }

    function buildFieldset(mainLabel, items, name, typeName, loaderCreator, labelFunc) {
        var fs = document.createElement("fieldset");
        var legend = document.createElement("legend");
        legend.innerHTML = mainLabel;
        fs.appendChild(legend);
        this.roadtypes = {};
        items.forEach(function(r, i){
            var cb = document.createElement("input");
            cb.type = typeName;
            cb.name = name;
            cb.value = r;
            if( typeName === "radio" ) {
                cb.checked = true;
            } else {
                cb.checked = false;
            }
            cb.onchange = loaderCreator(r);
            fs.appendChild(cb);
            var label = labelFunc(r);
            fs.appendChild(document.createTextNode(label + " "));
            this.roadtypes[r] = cb;
            if( i > 0 && (i%4) == 0 ) {
                fs.appendChild(document.createElement("br"));
            }
        }, this);

        return fs;
    }

    CubesetForm.prototype.addCubeSets = function(cubesets) {
        console.log("Cubesets:", cubesets);
        var self = this;

        // Remove the dummy Loading message.
        while(this.form.firstChild) {
            this.form.removeChild(this.form.firstChild);
        }

        // Setup the forms.
        this.set_categories = cubesets.categories;
        var tmp_categories = cubesets.categories.slice();
        var all = "all";
        tmp_categories.push(all);
        this.form.appendChild(
            buildFieldset("Categories", tmp_categories, "roadtype", "checkbox", function(name)  {
                return function(e) {
                    if( e.target.checked ) {
                        if( name === all ) {
                            self.set_categories.forEach(function(c) {
                                self.callbacks.category("roads", c);
                            });
                        } else {
                            self.callbacks.category("roads", name);
                        }
                    }
                }
            },
            cleanLabel)
        );

        var namedRegionFilter = function(f) {
            if( f.properties.name ) {
                return true;
            }
            return false;
        }

        var geoFormat = new ol.format.GeoJSON();
        function geoJsonToOlFeature(g) {
            return geoFormat.readFeature(g);
        }

        var namedRegions = cubesets.regions.features
            .filter(namedRegionFilter)
            .map(geoJsonToOlFeature);
        this.form.appendChild(
            buildFieldset("Named Regions", namedRegions, "namedregion", "checkbox", function(feature)  {
                return function(e) {
                    if( e.target.checked ) {
                        self.callbacks.region(feature);
                    }
                }
            },
            function(feature) { return feature.get("name"); })
        );

        // Operation to use when building.
        this.form.appendChild(document.createTextNode("Build Region Operation "));
        var opCombo = document.createElement("select");
        opCombo.name = "operations";
        // Add default query region set operation.
        var opt = document.createElement("option");
        opt.value = this.QueryRegionCommand;
        opt.text = "Query Region Set";
        opCombo.appendChild(opt);
        // Add supported server operations.
        cubesets.operations.forEach(function(op) {
            opt = document.createElement("option");
            opt.value = op;
            opt.text = cleanLabel(op);
            opCombo.appendChild(opt);
        });
        this.operation = opCombo.options[opCombo.selectedIndex].value;
        opCombo.onchange = function(e) {
            self.operation = e.target.value;
        }
        this.form.appendChild(opCombo);
    }

    return CubesetForm;
});