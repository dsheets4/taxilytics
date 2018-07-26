define([],
function() {
    var HelpForm = function(helpHtml) {
        this.form = document.createElement('div');
        if( helpHtml ) {
            this.form.innerHTML = helpHtml;
        }
        else {
            this.form.innerHTML = `
            <table class="help">
                <tr><th>Group</th><th>Control</th><th>Description</th></tr>

                <tr><td rowspan=2>Selection</td><td>Single Click</td><td>Select features under the mouse</td></tr>
                <tr><td>Hold Alt+Shift, Click+Drag</td><td>Select features intersecting the drawn box</td></tr>

                <tr><td rowspan=4>Map Manipulation</td><td>Double Click</td><td>Zoom in one level at clicked area</td></tr>
                <tr><td>Click, Hold, Drag</td><td>Pan</td></tr>
                <tr><td>Mouse wheel rotate</td><td>Zoom In/Out</td></tr>
                <tr><td>Hold Shift, Click+Drag</td><td>Zoom into area within drawn box</td></tr>

                <tr><td rowspan=4>Menus</td><td>Layers</td><td>Control visibility and opacity of layers.  Change maps</td></tr>
                <tr><td>Fitlers</td><td>Not currently functional</td></tr>
                <tr><td>Info</td><td>Shows information about selected items</td></tr>
                <tr><td>Help</td><td>This menu!</td></tr>
            </table>
            `;
        }
    }
    return HelpForm;
});
