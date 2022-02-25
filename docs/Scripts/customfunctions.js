
CustomFunctions.associate("showData", showDataEx);


function Add(first, second) {

    

   return new OfficeExtension.Promise(function (resolve, reject) {
   
       //var tmp = first * second;
       var tmp = [[5, 2, 3, 4]]; 
   
       resolve(tmp);
       
   });

}

function showData(url) { 
    return showDataEx(url, "", "", "1", false);
}

function showDataEx(url, type, fieldname, showheadersStr) {
   return showDataEx2(url, type, fieldname, showheadersStr, false);
}

function showDataEx2(url, type, fieldname, showheadersStr, writetoSelected) {

 
 

   var tmp = [[1, 2, 3, 4]];
   var showheaders = false;
   
   if (showheadersStr.length === 1) {
   
       if (showheadersStr[0] === "1") {
           showheaders = true;
       }
   }
   
   ///url = "https://api.xbrl.us/api/v1/entity/report/search?fields=entity.*,report.id,entity.limit(40)";
   //var url = "https://api.xbrl.us/api/v1/fact/search?entity.cik=0000320193&concept.local-name=Assets&fact.has-dimensions=false&fact.ultimus=true&period.fiscal-period=Y&fields=entity.name,fact.value,fact.decimals,unit,report.filing-date.sort(DESC),concept.local-name,period.fiscal-year,dts.id,report.sec-url";
   console.log("showData:" + url);
   return new OfficeExtension.Promise(function (resolve, reject) {
    
        token = window.accessToken;
        var myHeaders = new Headers();
        myHeaders.append("Authorization", "Bearer " + token);

        //var tmp = first * second;
        var tmp = [[token, 2, 3, 4]];

  
   
        var requestOptions = {
            method: 'GET',
            headers: myHeaders,
            redirect: 'follow'
        };
   
        var res = fetch(url, requestOptions)
            .then(function (response) { return response.text() })
            .then(function (result ) {
                console.log("showData res");
                console.log(result);
                var json = JSON.parse(result);
                var formatRes = fullResponse(json, type, fieldname, showheaders);
                var disp = displayData(formatRes, type, fieldname, showheaders);

                if (writetoSelected) {
                    Excel.run(function (ctx) {
                        // Create a proxy object for the active sheet
                        var range = ctx.workbook.getSelectedRange();
                        range.load();
                        ctx.sync();

                        //var results = [disp];
                   

                        let newrange = range.getResizedRange(disp.length - 1, disp[0].length - 1);

                        // Queue a command to write the sample data to the worksheet
                        newrange.values = disp;

                        // Run the queued-up commands, and return a promise to indicate task completion
                        return ctx.sync();
                    }).catch(errorHandler);

                }
                
                resolve(disp);
   
   
            })
            .catch(function (error) {
                console.error(error);
                var tmp = [[token, "err: " + error, url, 4]];
                resolve(tmp);
                CheckToken();
            });
   
   
   
     
   
   });
}

function displayData(info, mytype, fieldname, showheaders) {
    if (info == undefined) {
        return "[There is no data for this query.]";
    }
    if (showheaders == undefined || typeof (showheaders) != 'boolean') {
        showheaders = true;
    }

    var resp = [];

    // Make sure there's at least one record 
    if (!isEmpty(info)) {
        // Determine the header from the first response and write to output
        var names = Object.keys(info);

        // if the first name is a zero then the array isn't one dimensional
        if (names[0] == "0") {
            //Logger.log('first');
            if (info[0] != null) {
                // Logger.log("is not null");
            }

            // find the first record with information if it's an object
            var x;
            // determine if multidimensional object
            if (typeof info[0] == "object") {
                // determine if with sequence or not
                if (inKeys('sequence 1', Object.keys(info[0]))) {
                    for (x = 0; x < info.length; x++) {
                        //if (!inKeys('field', Object.keys(info[x]))) break;
                        if (info[x] != null) {
                            break;
                        }
                    }
                } else {
                    x = 0
                }
            } else {
                if (mytype != "fields" && showheaders && fieldname != undefined) {
                    info.unshift(fieldname);
                }
            }

            if (!mytype || (info[x] != null && typeof info[x] == "object")) {
                /*if (info[x] != undefined) {
                  names = Object.keys(info[x]);
                else {
                  names = Object.keys(info[0]);
                }*/
                names = (info[x] != undefined ? Object.keys(info[x]) : Object.keys(info[0]));

                //if (names.length > 0) {
                //    names[0] = fieldname;
                //}


                for (var i = 0; i < names.length; i++)
                    if (names[i] == 'field') {
                        //Logger.log("modded");
                        names[i] = fieldname;
                    }


                if (showheaders) {

                    if (names.length === 0) {

                        names[0] = "";
                    }
                    resp.push(names);
                }
                resp = resp.concat(dd(info));
            } else {
                return pivot(info);
            }
        } else {
            //Logger.log('second');
            if (showheaders) resp.push(names);
            var output = [];
            var max = 0;
            for (var x = 0; x < names.length; x++) {
                if (names[x] != 'fields') {
                    output[x] = dd(info[names[x]], true);
                } else {
                    output[x] = "";
                }
                if (output[x].length > max)
                    max = output[x].length;
            }
            for (var x = 0; x < max; x++) {
                line = [];
                for (var y = 0; y < names.length; y++) {
                    line.push(output[y][x]);
                }
                resp.push(line);
            }
        }
    } else {
        line = [];
        if (info.length > 3) {
            line.push (info);
        }
        else
            line.push("There is no data for this query.");
            resp.push(line); 
    }

    return resp;
}

function pivot(info) {
    var resp = [];

    for (var index = 0; index < info.length; index++) {
        var row = [];

        row.push(info[index]);
        resp.push(row);
    }

    return resp;

}


function dd(info, oned) {
    var resp = [];

    for (var index = 0; index < info.length; index++) {
        // loop through each data item
        switch (typeof info[index]) {
            case "object":
                var line = [];
                Object.keys(info[0]).forEach(function (fieldname) {
                    // add each value to array
                    var field_type = typeof info[index][fieldname];
                    switch (field_type) {
                        case "object":
                            if (info[index][fieldname] != null) {
                                line.push(flattenObject(info[index][fieldname]));
                            } else {
                                line.push(' ');
                            }
                            break;
                        default:
                            var tmp = info[index][fieldname];

                            if (tmp != null && tmp != "null" ) {



                                if (tmp[0] === '<') {


                                    tmp = '<![CDATA[' + tmp.substring(0, 60000) + ']>';
                                }
                                else if (tmp.length > 255) {

                                    console.log(tmp.length);
                                    tmp = tmp.substring(0, 60000);
                                }

                            }
                            else {
                                tmp = ' ';
                            }

                            line.push(tmp);
                    }
                });

                if (line.length === 0) {

                    line.push("");
                }

                resp.push(line);
                
                break;
            default:
                resp.push(info[index]);
        }
    }

  
    return resp;

}

function isEmpty(obj) {

    // null and undefined are "empty"
    if (obj == null) return true;
    // Assume if it has a length property with a non-zero value
    // that that property is correct.

    // If it isn't an object at this point
    // it is empty, but it can't be anything *but* empty
    // Is it empty?  Depends on your application.
    if (typeof obj !== "object") return true;

    // Otherwise, does it have any properties of its own?
    // Note that this doesn't handle
    // toString and valueOf enumeration bugs in IE < 9
    for (var key in obj) {
        if (hasOwnProperty.call(obj, key)) return false;
    }

    if (obj.length > 0) return false;
    if (obj.length === 0) return true;

    return true;
}

/**
 * Copyright 2018 - present, XBRL US, Inc.  All rights reserved.
 * Flattens an array into a string
 *
 * @param {array} item
 * @param {boolean} recursive Tells function if this call is being recursed
 * @returns {string}
 */
function flattenObject(item, recursive) {
    value = " ";

    if (item == null || typeof (item) != 'object') return "";

    Object.keys(item).forEach(function (key) {
        switch (typeof item[key]) {
            case "object":
                value += key + " : " + flattenObject(item[key], true) + " ";
                break;
            default:
                value += key + " : " + item[key] + "; ";
        }
    });

    value = "( " + value + " )";

    return value;

}

function inKeys(needle, keys) {
    var found = false;

    if (typeof keys == 'object') {
        keys.forEach(function (item) {
            if (needle == item) {
                found = true;
            }
        });
    }

    return found;
}

/* 
 *  Takes the array and translates it into a tree of fields
 *    that exist in the result
 *
 * @param {array} data The array of information retreived from the API without
 *    the paging section
 * @param {integer} level Keeps track of the level it's at when recursing
 * @returns {array} List of fields from the data
 *
 */
function buildTree(data, level) {
    if (level == null) {
        level = 0;
    }
    var list = [];

    for (var key in data) {
        if (key == "0") {
            info = buildTree(data[0], level);
            list = concat(list, info);
            return list;
        } else {
            list.push(dashes(level) + key);
            if (typeof data[key] == "object") {
                info = buildTree(data[key], level + 1);
                list = concat(list, info);
            }
        }
    }

    return list;
}





/**
 * Returns the data for the field listed in field names.  It may need to recurse into 
 *   the data depending on the levels of field names.
 * 
 * @param {array} data Information from the API without the metadata
 * @param {string} fieldnames The fieldname of the data that should be returned.  If the fieldname
 *                            is at a lower level the names "leading" to it should be delimited
 *                            with a "/"
 * @returns {array} Data for field requested
 */
function returnValue(data, fieldnames) {
    var names = fieldnames.split("/");

    var result = [];
    if (typeof data[0] != "undefined") {
        // deal with array

        for (var i = 0; i < data.length; i++) {
            var info = data[i];
            result.push(returnValue(info, fieldnames));
        }
    } else {
        // is object?
        if (typeof data == "object") {
            // deal with object

            for (var j = 0; j < names.length; j++) {
                var name = names[j];
                var found = false;
                //for (var k = 0; k < data.length; k++) {
                for (var info in data) {
                    //var info = data[k];
                    if (info == name) {
                        found = true;
                        if (names.length == 1) {
                            return data[info];
                        } else {
                            if (data[info] != null) {
                                return returnValue(data[info], names.slice(1).join("/"));
                            } else {
                                // information is not available, return string here
                                return "null";
                            }
                        }
                    }
                };
                if (!found)
                    return "Name not found";
            }
        } else {
            // it's not an object
            for (var name in names) {
                if (info == name) {
                    if (names.length == 1) {
                        return data[info];
                    } else {
                        return returnValue(data[info], names.slice(1));
                    }
                }
            }
        }
    }

    return result;
}


/** 
 * Strips the metadata from the submitted array and returns the rest, or returns the field tree,
 *   or only the data from the requested field.
 *
 * FUTURE FEATURE: add paging support
 *
 * @param {array} data Information returned from the API in array format 
 * @param {string} type [optional] (blank, fields, name): Determines how the information will be returned
 *     blank: returns "data" without the metadata,
 *     fields: returns a tree of the fields in the data array, 
 *     name: used with "fieldname" to return only the information related to the specified field
 * @param {string} fieldname [optional] The name of the field that should be returned.  The different 
 *     levels are separated by a "/"
 * @param {boolean} showheaders [optional] Determines if the headers are displayed in the output 
 * @returns {array} the results in a format appropriate to be displayed on the sheet
 */
function fullResponse(data, type, fieldname, showheaders) {
    if (data == undefined) {
        return "Error in output";
    }
    if (type == undefined) {
        type = "default";
    }
    if (showheaders == undefined || typeof (showheaders) != 'boolean') {
        showheaders = true;
    }

    if (data.error) {
        if (data.error_description) {
            return data['error_description'];
        } else {
            return data['error'];
        }
    }

    data = handle(data);

    switch (type) {
        case "fields":
            // returns a tree of the information
            info = buildTree(data);
            break;
        case "name":
            if (fieldname == undefined) {
                return "No fieldname defined";
            }

            var mainReturn = [];
            var d = returnValue(data, fieldname);

            if (typeof d[0] == "object") {
                d = formatmulti(d);
            } else {
            }

            return d;

            if (info == undefined)
                return "There was an error retrieving data";
            break;
        default:
            info = data;

    }
    return info;

    return "There was an error";

}


/*
 * Copyright 2018 - present, XBRL US, Inc.  All rights reserved. 
 * Looks at the data retrieved from the API and examines the elements.  It recurses through the 
 * object removing the "paging" array if it exists and returns it with just the data. 
 
 * @param {array} data An array of data retrieved directly from the  API
 * @returns {array} If it's passed an object(array) it returns the 
 *    array.  Otherwise it returns the object
 *
 */
function handle(data) {
    if (typeof data == 'object') {
        var item = [];
        Object.keys(data).forEach(function (key) {
            switch (key) {
                case "paging":
                    break;
                default:
                    if (data[key] != null && typeof data[key] == "object") {
                        value = handle(data[key]);
                        if (key == "data") {
                            return item = value;
                        } else {
                            return item[key] = value;
                        }
                    } else {
                        item[key] = data[key];
                    }
            }
        });

        return item;
    } else {
        return data;
    }

}




/*
 * Returns a string of dashes based on the number passed
 *
 * @param num, int, the number of dashes that should be 
 *   returned in the string
 *
 */
function dashes(num) {
    var dash = "";
    for (var x = 0; x < num; x++) {
        dash += "-";
    }
    if (dash.length > 0) {
        dash = "   " + dash + " ";
    }

    return dash;
}


/** 
 * Appends array2 to array1
 *
 * @param {array} array1
 * @param {array} array2
 * @returns {array}
 */
function concat(array1, array2) {
    for (var x = 0; x < array2.length; x++) {
        array1.push(array2[x]);
    }

    return array1;
}


/** 
 * Appends array2 to array1.  These are named arrays.
 *
 * @param {array} array1
 * @param {array} array2
 * @returns {array}
 */
function concat_nv(array1, array2) {
    for (var name in array2) {
        array1[name] = array2[name];
    }

    return array1;
}

function concat_array(array1, array2) {
    var new_array = [];
    for (var x = 0; x < array1.length; x++) {
        new_array.push(array1[x]);
    }
    for (var x = 0; x < array2.length; x++) {
        new_array.push(array2[x]);
    }

    return new_array;
}

/**
 * Recursed into an array and for each level adds a sequence field 
 *
 * @param {array} An array of multidimensional data
 * @param {integer} Number that's keeps track of what level (or sequence) the iteration
 *                  of this function is dealing with
 * @returns {array}
 */
function formatmulti(data, level) {
    if (level == undefined)
        level = 1;

    var new_data = [];
    if (typeof data == "object") {

        if (Array.isArray(data) && Object.keys(data)[0] == 0) {
            var m = [];
            for (var seq in data) {
                info = formatmulti(data[seq], level + 1);
                var m = blarg(m, info, level, parseInt(seq));
            }
            return m;
        } else {
            return data;
        }

    } else {
        if (data == null) {
            data = "null";
        }
        return data;
    }

    return new_data;
}



function blarg(m, info, level, seq) {
    if (Array.isArray(info) && Object.keys(info)[0] == 0) {

        var ar = [];
        for (var i in info) {
            //console.log('grr');
            var mod = [];
            mod['sequence ' + level] = seq + 1;
            for (var key in info[i]) {
                //console.log('key: ' + key);
                mod[key] = info[i][key];
            }
            ar.push(mod);
        }

        m = concat_array(m, ar);
        return m;
        return ar;
    } else {
        var mod = [];
        mod['sequence ' + level] = seq + 1;
        if (typeof info == "object" && info != null) {
            for (var key in info) {
                //console.log('key: ' + key);
                mod[key] = info[key];
            }
        } else {
            if (info == null) {
                mod = ["null"];
            }
            mod['field'] = info
        }

        m.push(mod);
        return m;
        return mod;
    }

}