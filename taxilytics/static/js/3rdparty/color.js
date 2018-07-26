
if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) { 
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}
	
define(['js/3rdparty/tinycolor'], function(tc){
	
	var _colors = [
	          "#FF0000",  // Red
	          "#00FF00",  // Green
	          "#0000FF",  // Blue
	          "#FF00FF",  // Magenta
	          "#00FFFF",  // Cyan
	          "#FF6400",  // Orange
	          "#006666",  // Blue-green
	          "#A1501C",  // Brown
	          "#cc3d50", "#008000",
	          "#808000", "#008080", "#800000", "#800080", "#808080",
	          "#990054", "#FFA500", "#FFC0CB",
	          "#CD853F", "#F08080", "#006400", "#A0FFFF", "#000080",
	          "#CDCD3F", "#F0F080", "#346434", "#00AFFF", "#800080",
	          "#CD85CD", "#F080F0", "#646400", "#00FFFF", "#008080",
	          "#F08080", "#006464", "#00FFAF", "#800000",
	          "#CD853F", "#808080", "#70F7F7", "#008000",
	          "#85853F", "#F0F080", "#0064FF", "#007F7F", "#343480",
	          "#CD8585", "#648080", "#A064A0", "#88FFFF", "#A0A080",
	          "#ff9999", "#cc7a7a", "#995c5c", "#ff4d4d", "#cc3d3d",
	          "#992e2e", "#ff0000", "#cc0000", "#991400", "#ffb499",
	          "#cc907a", "#996c5c", "#ff7c4d", "#cc633d", "#994a2e",
	          "#ff4400", "#cc3600", "#ffc299", "#cc9b7a", "#99745c",
	          "#ff944d", "#cc763d", "#99592e", "#ff6600", "#cc5200",
	          "#993d00", "#ffcf99", "#997c5c", "#ffac4d", "#cc893d",
	          "#99672e", "#ff8800", "#cc6d00", "#995200", "#ccb17a",
	          "#99855c", "#ffc44d", "#cc9c3d", "#ffaa00", "#cc8800",
	          "#996600", "#ffeb99", "#99842e", "#ffcc00", "#cca300",
	          "#ffee00", "#ccbe00", "#998f00", "#f8ff99", "#c2cc3d",
	          "#eeff00", "#bccc7a", "#8d995c", "#84992e", "#ccff00",
	          "#9ccc3d", "#67992e", "#88ff00", "#c2ff99", "#9bcc7a",
	          "#74995c", "#63cc3d", "#3c992e", "#00ff00", "#99ffa7",
	          "#00cc1b", "#5c996c", "#3dcc63", "#7acc9b", "#00ff66",
	          "#99ffcf", "#3dcc89", "#009952", "#5c9985", "#2e9975",
	          "#00ffaa", "#99ffeb", "#7accbc", "#3dccaf", "#00ffcc",
	          "#5c9995", "#00ffee", "#00998f", "#99f8ff", "#3dc2cc",
	          "#00eeff", "#008f99", "#3dafcc", "#00ccff", "#007a99",
	          "#99ddff", "#7ab1cc", "#5c8599", "#3d9ccc", "#00aaff",
	          "#006699", "#99cfff", "#3d89cc", "#0088ff", "#005299",
	          "#7a9bcc", "#5c7499", "#3d76cc", "#0066ff", "#003d99",
	          "#99b4ff", "#3d63cc", "#0044ff", "#0036cc", "#002999",
	          "#3d50cc", "#001bcc", "#9999ff", "#5c5c99", "#0000ff",
	          "#857acc", "#7c4cff", "#633dcc", "#c299ff", "#592e99",
	          "#3d0099", "#a67acc", "#6d00cc", "#c44dff", "#9c3dcc",
	          "#aa00ff", "#660099", "#eb99ff", "#8d5c99", "#c23dcc",
	          "#8f0099", "#992e92", "#ff00ee", "#ff99eb", "#cc7abc",
	          "#cc3daf", "#ff00cc", "#995c85", "#992e75", "#ff00aa",
	          "#cc0088", "#ff99cf", "#cc7aa6", "#ff0088", "#cc3d76",
	          "#992e59", "#ff0066", "#cc0052", "#99003d", "#ff99b4",
	          "#995c6c", "#ff0044", "#cc0036", "#990029", "#ff4d64",
	         ]
	
	function _randomColor(){
	    r = parseInt(Math.random()*255)
	    g = parseInt(Math.random()*255)
	    b = parseInt(Math.random()*255)
	    
	    return "#" + tc({"r": r, "g": g, "b": b}).toHex()
	}
	
	return {
		ColorTable: function() {
			this.colors = _colors.slice(0), // Create copy
			this.GetColorString = function( nIdx ) {    
			    // For a negative index, black is always returned
			    if( nIdx < 0 ) {
			        return "#000000";
			    }
			
			    // Check if the color already exists in the color table
			    if( nIdx > this.colors.length-1 ) {
			        while( this.colors.length-1 < nIdx ) {
			            this.colors.push( _randomColor() );
			        }
			    }
			
			    // Return the requested color
			    return this.colors[nIdx];
			},
			this.GetColorStringRgb = function( nIdx ){
			    var c = tc(this.GetColorString(nIdx));
			    return c.toRgbString();
			},
			this.GetColorStringRgba = function( nIdx, alpha ){
			    var c = tc(this.GetColorString(nIdx));
			    c.setAlpha(alpha);
			    return c.toRgbString();
			}
		}
	}
});