define([],
function() {
    var InfoForm = function(format) {
        var self = this;
        this.info_obj = {};
        this.form = document.createElement('div');
        self.format = format;

        var table = document.createElement('table');
        var thead = document.createElement('thead');
        self.tbody = document.createElement('tbody');
        table.appendChild(thead);
        table.appendChild(self.tbody);
        var row = document.createElement('tr');
        self.format.header.forEach(function(v, i) {
            var td = document.createElement('th');
            td.onclick = function() {
                sort_table(self.tbody, i, -1);
            };
            td.innerHTML = v;
            row.appendChild(td);
        });
        thead.appendChild(row);
        this.form.appendChild(table);

        // Adapted from:
        // http://codereview.stackexchange.com/questions/37632/sorting-an-html-table-with-javascript
        function sort_table(tbody, col, asc){
            var rows = tbody.rows
            var rlen = rows.length
            var arr = new Array()
            var i, j, cells, clen;
            // fill the array with values from the table
            for(i = 0; i < rlen; i++) {
                cells = rows[i].cells;
                clen = cells.length;
                arr[i] = new Array();
                    for(j = 0; j < clen; j++){
                        arr[i][j] = cells[j].innerHTML;
                    }
            }
            // sort the array by the specified column number (col) and order (asc)
            arr.sort(function(a, b){
                var fA = parseFloat(a[col]) || a[col];
                var fB = parseFloat(b[col]) || b[col];
                return (fA == fB) ? 0 : (fA > fB) ? asc : -1*asc;
            });
            for(i = 0; i < rlen; i++){
                arr[i] = "<td>"+arr[i].join("</td><td>")+"</td>";
            }
            self.tbody.innerHTML = "<tr>"+arr.join("</tr><tr>")+"</tr>";
        }

        this.selectCallback = function(evt) {
            var props = evt.element.getProperties();
            var id = evt.element.getId();
            var type;
            if( 'info' in props ) {
                type = props.info.type;
            } else {
                type = undefined;
            }
            if( !(id in info_obj) ) {
                if( self.format ) {
                    info_obj[id] = format.format(evt.element);
                } else {
                    info_obj[id] = id;
                }
            }
            if( self.form ) {
                var info = [];
                for( let id in info_obj ) {
                    info.push(info_obj[id]);
                }
                info.forEach(function(o){
                    var row = document.createElement('tr');
                    o.forEach(function(v) {
                        var td = document.createElement('td');
                        td.innerHTML = v;
                        row.appendChild(td);
                    });
                    self.tbody.appendChild(row);
                });
            }
        };

        this.clearCallback = function() {
            info_obj = {};
            if( self.tbody ) {
                while (self.tbody.firstChild) {
                    self.tbody.removeChild(self.tbody.firstChild);
                }
            }
        }
        this.clearCallback();
    };

    return InfoForm;
});