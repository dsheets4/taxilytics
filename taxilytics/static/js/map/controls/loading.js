define(['ol'], function(ol) {

    var drawPoly = {};

    var LoadingControl = function(opt_options) {
        var options = opt_options || {};
        options.cancelFunction = options.cancelFunction || function(){};

        var button = document.createElement('button');
        button.innerHTML = '';

        var self = this;
        function onCancel() {
            if( confirm("Are you sure you want to cancel loading?") ) {
                options.cancelFunction();
                self.endLoad();
            }
        }

        button.addEventListener('click', onCancel, false);
        button.title = 'Loading indicator, click to cancel current load';
        button.className = "load-control";

        var img = document.createElement('img');
        img.src = "../../../static/img/loading.gif";
        img.width = "20";
        button.appendChild(img);

        this.element = document.createElement('div');
        this.element.className = "load-control ol-unselectable ol-control";
        this.element.appendChild(button);
        this.element.style.display = "block";

        ol.control.Control.call(this, {
            element: this.element,
            target: options.target,
        });
    };
    ol.inherits(LoadingControl, ol.control.Control);

    LoadingControl.prototype.startLoad = function() {
        this.element.style.display = "block";
    }

    LoadingControl.prototype.endLoad = function() {
        this.element.style.display = "none";
    }

    LoadingControl.prototype.cancel = function() {
        this.element.style.display = "none";
    }

    return LoadingControl;
});