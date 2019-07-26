/**
 * Array.insert, inserts an array into the the array.
 * @param index Index to insert at.
 * @param arr The array to insert.
 * @returns {Array} The array (this).
 */
Array.prototype.insert = function(index, arr){
	var i;
	for (i=0; i < arr.length; i++) {
		this.splice(index+i, 0, arr[i]);
	}
	return this;
};

/**
 * Date.parse with progressive enhancement for ISO 8601 <https://github.com/csnover/js-iso8601>
 * (c) 2011 Colin Snover <http://zetafleet.com>
 * Released under MIT license.
 */
(function (Date, undefined) {
    var origParse = Date.parse, numericKeys = [ 1, 4, 5, 6, 7, 10, 11 ];
    Date.parse = function (date) {
        var timestamp, struct, minutesOffset = 0;

        // ES5 15.9.4.2 states that the string should attempt to be parsed as a Date Time String Format string
        // before falling back to any implementation-specific date parsing, so that's what we do, even if native
        // implementations could be faster
        //              1 YYYY                2 MM       3 DD           4 HH    5 mm       6 ss        7 msec        8 Z 9     10 tzHH    11 tzmm
        if ((struct = /^(\d{4}|[+\-]\d{6})(?:-(\d{2})(?:-(\d{2}))?)?(?:T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{3}))?)?(?:(Z)|([+\-])(\d{2})(?::(\d{2}))?)?)?$/.exec(date))) {
            // avoid NaN timestamps caused by 'undefined' values being passed to Date.UTC
            for (var i = 0, k; (k = numericKeys[i]); ++i) {
                struct[k] = +struct[k] || 0;
            }

            // allow undefined days and months
            struct[2] = (+struct[2] || 1) - 1;
            struct[3] = +struct[3] || 1;

            if (struct[8] !== 'Z' && struct[9] !== undefined) {
                minutesOffset = struct[10] * 60 + struct[11];

                if (struct[9] === '+') {
                    minutesOffset = 0 - minutesOffset;
                }
            }

            timestamp = Date.UTC(struct[1], struct[2], struct[3], struct[4], struct[5] + minutesOffset, struct[6], struct[7]);
        }
        else {
            timestamp = origParse ? origParse(date) : NaN;
        }

        return timestamp;
    };
}(Date));


// Source: https://gist.github.com/938823
if (!Object.keys) {
	Object.keys = function(object) {
		var results = [], property;
		function abc(property) {
			if (({}).hasOwnProperty.call(object, property)) {
				results.push(property);
			}
		}
		for (property in object) {
			abc(property);
		}
		if (!({
			valueOf : ''
		}).propertyIsEnumerable('valueOf')) {
			'setYear constructor toString valueOf toLocaleString isPrototypeOf propertyIsEnumerable hasOwnProperty'
					.replace(/\S+/g, abc);
		}
		return results;
	};
}

// Source http://stackoverflow.com/questions/439463/how-to-get-get-and-post-variables-with-jquery
// Ates Goral
function getQueryParams(qs) {
	qs = qs.split("+").join(" ");
	var params = {},
		tokens,
		re = /[?&]?([^=]+)=([^&]*)/g;

	while (tokens = re.exec(qs)) {
		params[decodeURIComponent(tokens[1])]
			= decodeURIComponent(tokens[2]);
    }

	return params;
}

// http://www.abeautifulsite.net/blog/2011/11/detecting-mobile-devices-with-javascript/
window.isMobile = {
	Android: function() {
		return navigator.userAgent.match(/Android/i);
	},
	BlackBerry: function() {
		return navigator.userAgent.match(/BlackBerry/i);
	},
	iOS: function() {
		return navigator.userAgent.match(/iPhone|iPad|iPod/i);
	},
	Opera: function() {
		return navigator.userAgent.match(/Opera Mini/i);
	},
	Windows: function() {
		return navigator.userAgent.match(/IEMobile/i);
	},
	any: function() {
		return (isMobile.Android() || isMobile.BlackBerry() || isMobile.iOS() || isMobile.Opera() || isMobile.Windows());
	}
};

// modified from fnReloadAjax by Allan Jardine.
$.fn.dataTableExt.oApi.fnReloadAAData = function ( oSettings, aaData, fnCallback, bStandingRedraw )
{
    this.oApi._fnProcessingDisplay( oSettings, true );
    var that = this;
    var iStart = oSettings._iDisplayStart;

    /* Clear the old information from the table */
    that.oApi._fnClearTable( oSettings );

    /* Got the data - add it to the table */

    for ( var i=0 ; i<aaData.length ; i++ )
    {
        that.oApi._fnAddData( oSettings, aaData[i] );
    }

    oSettings.aiDisplay = oSettings.aiDisplayMaster.slice();

    if ( typeof bStandingRedraw != 'undefined' && bStandingRedraw === true )
    {
        oSettings._iDisplayStart = iStart;
        that.fnDraw( false );
    }
    else
    {
        that.fnDraw();
        oSettings._iDisplayStart = iStart;
        that.fnDraw( false );
//      oSettings.oApi._fnCalculateEnd(oSettings);
//      oSettings.oApi._fnDraw(oSettings);
    }

    that.oApi._fnProcessingDisplay( oSettings, false );

    /* Callback user function - for event handlers etc */
    if ( typeof fnCallback == 'function' && fnCallback != null )
    {
        fnCallback( oSettings );
    }
};

jQuery.extend( jQuery.fn.dataTableExt.oSort, {
    "cnumeric-pre": function ( a ) {
        if (a === 'NA') {
            return Infinity;
        }
        return parseFloat( a );
    },

    "cnumeric-asc": function ( a, b ) {
        return ((a < b) ? -1 : ((a > b) ? 1 : 0));
    },

    "cnumeric-desc": function ( a, b ) {
        return ((a < b) ? 1 : ((a > b) ? -1 : 0));
    }
} );

/**
 * https://stackoverflow.com/questions/2573521/how-do-i-output-an-iso-8601-formatted-string-in-javascript
 * Implements Date.toISOString if not implemented in browser already
 * @author Anatoly Mironov
 */
if ( !Date.prototype.toISOString ) {
    ( function() {

        function pad(number) {
            var r = String(number);
            if ( r.length === 1 ) {
                r = '0' + r;
            }
            return r;
        }

        Date.prototype.toISOString = function() {
            return this.getUTCFullYear()
                + '-' + pad( this.getUTCMonth() + 1 )
                + '-' + pad( this.getUTCDate() )
                + 'T' + pad( this.getUTCHours() )
                + ':' + pad( this.getUTCMinutes() )
                + ':' + pad( this.getUTCSeconds() )
                + '.' + String( (this.getUTCMilliseconds()/1000).toFixed(3) ).slice( 2, 5 )
                + 'Z';
        };

    }() );
}