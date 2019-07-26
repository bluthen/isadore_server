//   Copyright 2010-2019 Dan Elliott, Russell Valentine
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.

function HTMLHelper() {}

HTMLHelper.actionButtons = ['<span class="action" data-action_type="delete">',
	                 '<img src="imgs/icon_delete.png" /><span>Delete</span> </span>',
	                 '<span class="action" data-action_type="edit">',
	                 '<img src="imgs/icon_edit.png" /><span>Edit</span> </span>'].join('');

HTMLHelper.spinner = '<img src="imgs/ajax-loader.gif" alt="Loading Spinner" />';

HTMLHelper.eqInArray = function(array, obj) {
	var ii;
	for(ii = 0; ii < array.length; ++ii) {
		if(array[ii] == obj) {
			return true;
		}
	}
	return false;
};
	
HTMLHelper.makeSelect = function(objects, displayKey, valueKey, multiple, sortKeys, sortCmp) {
	var selectStr, ii, dsortCmp;
	selectStr = [];
	if(multiple) {
		selectStr.push('<select multiple>');
	} else {
		selectStr.push('<select>');
	}
	if (sortKeys) {
		if (!sortCmp) {
			dsortCmp = function (a, b) {
				if (a[displayKey] < b[displayKey]) {
					return -1;
				}
				if (a[displayKey] > b[displayKey]) {
					return 1;
				}
				return 0;
			};
		} else {
			dsortCmp=sortCmp;
		}
		objects.sort(dsortCmp);
	}
	
	for(ii = 0; ii < objects.length; ++ii) {
		selectStr.push('<option value='+objects[ii][valueKey]+'>');
		selectStr.push(objects[ii][displayKey]);
		selectStr.push('</option>');
	}
	selectStr.push('</select>');
	
	return $(selectStr.join(''));
};

/**
 * Make a list out of a array of strings.
 * 
 * @param tolist
 *            A string array to have as items in the list.
 * @param ordered
 *            if exist will make a ordered list instead of unorderd.
 * @returns A DOM list element with contents to tolist as items.
 */
HTMLHelper.makeList = function(tolist, ordered) {
	var html, jj;
	html = [];
	if(ordered) {
		html.push('<ol>');
	} else {
		html.push('<ul>');
	}
	for(jj = 0; jj < tolist.length; ++jj) {
		html.push("<li>"+tolist[jj]+"</li>");
	}
	if(ordered) {
		html.push('</ol>');
	} else {
		html.push('</ul>');
	}
	return $(html.join(''));
};


HTMLHelper.padZeros = function(n, length) {
	var str, zeros, i;
	//snippet by MadBender from stackoverflow
	str = String((n > 0 ? n : -n));
	zeros = "";
	for (i = length - str.length; i > 0; i--) {
		zeros += "0";
	}
	zeros += str;
	return n >= 0 ? zeros : "-" + zeros;
};



/**
 * Given a javascript date object it'll return a string in format dmyHMS.
 * 
 * @param theDate
 *            The date object to get this string representation of.
 * @returns {string} The date as a parameter string argument.
 */
HTMLHelper.dateToParamString = function(theDate) {
    return theDate.toISOString();
};

HTMLHelper.dateToReadable = function(theDate) {
	//var d=theDate.getDate();
	//var m=theDate.getMonth()+1;
	//var y = theDate.getFullYear();
	//var H = theDate.getHours();
	//var M = theDate.getMinutes();
	//var S = theDate.getSeconds();
	return theDate.toString();
};

HTMLHelper.dateToReadableO2 = function(theDate, seconds) {
	var d=theDate.getDate();
	var m=theDate.getMonth()+1;
	var y = theDate.getFullYear();
	var H = HTMLHelper.padZeros(theDate.getHours(), 2);
	var M = HTMLHelper.padZeros(theDate.getMinutes(),2);
	var S = HTMLHelper.padZeros(theDate.getSeconds(), 2);
	var date = m+'/'+d+'/'+y+' '+H+":"+M;
	if(seconds) {
		date=date+":"+S;
	}
	return date;
};

HTMLHelper.dateToReadableO3 = function(theDate, seconds) {
    var d=theDate.getDate();
    var m=theDate.getMonth()+1;
    var y = theDate.getFullYear();
    var H = HTMLHelper.padZeros(theDate.getHours(), 2);
    var M = HTMLHelper.padZeros(theDate.getMinutes(),2);
    var S = HTMLHelper.padZeros(theDate.getSeconds(), 2);
    var date = m+'/'+d+' '+H+":"+M;
    if(seconds) {
        date=date+":"+S;
    }
    return date;
};


/**
 * Returns new date with time added or subtracted by the arguments
 * @param args key/value pairs listed below
 * @key date The date object we want to do time math on.
 * @key hours Hours to add or subtract(if negative) from date.
 * @key days Days to add or subtract(if negative) from date.
 */
HTMLHelper.datetimeDelta = function(args) {
	var h = 0;
	var d = 0;
	if(args.hours) {
		h = args.hours;
	} 
	if(args.days) {
		d = args.days;
	}
	return new Date(args.date.getTime() + h*3600000 + d*86400000);
};

/**
 * Takes a phone removes all whitespace from phone number. If 10 digits and not
 * start with 1 then will prefix 1. Returns null if invalid number.
 */
HTMLHelper.phoneToParam = function(phoneStr) {
	var cleaned = phoneStr.replace(/\W+/g, '');
	if(cleaned.length == 10 && cleaned[0] != 1) {
		cleaned='1'+cleaned;
		return cleaned;
	} else if(cleaned.length == 11 && cleaned[0] == 1) {
		return cleaned;
	} else {
		return null;
	}
};

/**
 * Takes pure 11 digit phone number and puts dashes in it. If not 11 digits just
 * returns parameter back.
 */
HTMLHelper.phoneToReadable = function(phoneStr) {
    var phone;
	if(!phoneStr) { 
		return ''; 
	}
	if(phoneStr.length != 11) {
		return phoneStr;
	}
	phone=[];
	phone.push(phoneStr[0]);
	phone.push('-');
	phone.push(phoneStr.substr(1,3));
	phone.push('-');
	phone.push(phoneStr.substr(4,3));
	phone.push('-');
	phone.push(phoneStr.substr(7,4));
	return phone.join('');
};

/** @returns {boolean} true if valid email format. */
HTMLHelper.validEmail = function(emailStr) {
	//Source: http://www.regular-expressions.info/email.html
	var regex = /^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,4}$/i;
	return regex.test(emailStr);
};

/** Takes key value parts and makes a parameter url out of them. */
HTMLHelper.makeParameters = function(args) {
	var ii, parmStr, keys, key;
	parmStr='';
	keys = Object.keys(args);
	for(ii = 0; ii < keys.length; ii++) {
		key = keys[ii];
		parmStr+=encodeURIComponent(key)+'='+encodeURIComponent(args[key])+'&';
	}
	return parmStr;
};

newDate = function(dateStr) {
	return new Date(Date.parse(dateStr));
};

function calendarRegister(object) {
	object.datetimepicker({
		constrainInput : true,
		hourGrid : 4,
		minuteGrid : 10
	});
	if(isMobile.any() && object.is('input')) {
		object.prop('readonly', true);
	}
}

function calendarImageRegister(object) {
	object.click(function(event) {
		$('#' + event.currentTarget.getAttribute('data-date_id')).datepicker(
				'show');
	});
}

