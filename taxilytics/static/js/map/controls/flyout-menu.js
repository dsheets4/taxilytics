define(['ol'], function(ol) {

    var FlyoutMenu = function(label, opt_options){

        var options = opt_options || {};
        var tipLabel = options.tipLabel ? options.tipLabel : '';
        var extraClassName = options.className ? options.className : '';
        this.form = options.form ? options.form : null;

        this.hiddenClassName = extraClassName + ' flyout-menu ol-unselectable ol-control ';
        if (this.isTouchDevice_()) {
            this.hiddenClassName += ' touch';
        }
        this.visibleClassName = this.hiddenClassName + " shown";

        var element = document.createElement('div');
        element.className = this.hiddenClassName;

        var button = document.createElement('button');
        button.innerHTML = label;
        button.title = tipLabel;
        element.appendChild(button);

        this.menu = document.createElement('div');
        this.menu.className = 'menu';
        element.appendChild(this.menu);

        if(this.form) {
            this.menu.appendChild(this.form);
        }

        var self = this;
        button.onmouseover = function(e) {
            self.showMenu();
        };

        this.clamped = false;
        button.onclick = function(e) {
            e = e || window.event;
            self.showMenu();
            e.preventDefault();
            self.clamped = !self.clamped;
        };

        element.onmouseout = function(e) {
            e = e || window.event;
            if (!self.menu.contains(e.toElement || e.relatedTarget) && !self.clamped) {
                self.hideMenu();
            }
        };

        ol.control.Control.call(this, {
            element: element,
            target: options.target
        });
    }
    ol.inherits(FlyoutMenu, ol.control.Control);

    FlyoutMenu.prototype.showMenu = function() {
        if (this.element.className != this.visibleClassName) {
            this.element.className = this.visibleClassName;
            if( !this.form ) {
                this.renderMenu();
            }
        }
    };

    FlyoutMenu.prototype.hideMenu = function() {
        if (this.element.className != this.hiddenClassName) {
            this.element.className = this.hiddenClassName;
        }
    };

    FlyoutMenu.prototype.renderMenu = function() {
        if( !this.form ) {
            this.form = document.createElement("div");
            this.form.innerHTML = "TODO: Implement renderMenu or provide an element to the constructor options."
            this.menu.appendChild(this.form);
        }
    };

    /**
    * @private
    * @desc Apply workaround to enable scrolling of overflowing content within an
    * element. Adapted from https://gist.github.com/chrismbarr/4107472
    */
    FlyoutMenu.prototype.enableTouchScroll_ = function(elm) {
       if(FlyoutMenu.isTouchDevice_()){
           var scrollStartPos = 0;
           elm.addEventListener("touchstart", function(event) {
               scrollStartPos = this.scrollTop + event.touches[0].pageY;
           }, false);
           elm.addEventListener("touchmove", function(event) {
               this.scrollTop = scrollStartPos - event.touches[0].pageY;
           }, false);
       }
    };

    /**
     * @private
     * @desc Determine if the current browser supports touch events. Adapted from
     * https://gist.github.com/chrismbarr/4107472
     */
    FlyoutMenu.prototype.isTouchDevice_ = function() {
        try {
            document.createEvent("TouchEvent");
            return true;
        } catch(e) {
            return false;
        }
    };

    return FlyoutMenu;
});
