define(["js/apps"],
function(apps) {
    var FilterForm = function(controls) {
        var self = this;
        this.form = document.createElement('div');
        if( controls ) {
            this.form.appendChild(controls);
        }
        else {
            this.form.innerHTML = "No form type was given.";
        }
    }
    return FilterForm;
});
