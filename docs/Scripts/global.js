var clientSecret; 
var clientId;
var token;
var endpoint;

 
function rawCall(url, format) {

    if (url === undefined) {
        throw "Error: No Url Defined";
    }

    if (format === undefined) {
        format = 'array';
    }

       

    OfficeRuntime.storage.getItem("accesstoken").then(function (result) {


        var myHeaders = new Headers();
        myHeaders.append("Authorization", "Bearer " + result);

        var requestOptions = {
            method: 'GET',
            headers: myHeaders,
            redirect: 'follow'
        };
        
        fetch(endpoint + "entity/report/search?fields=entity.*,report.id,entity.limit(40)", requestOptions)

            .then(function (response) { response.text() })
            .then(function (result) {
                console.log(result)
            })
            .catch(function (error) { console.log('error', error) });



    }, function (error) {
        showNotification("Error", error);
    });
    
}










//
/**
 * Stores a key-value pair into OfficeRuntime.storage.
 * @customfunction
 * @param {string} key Key of item to put into storage.
 * @param {*} value Value of item to put into storage.
 * @return {string} status 
 */
function storeValue(key, value) {
    return OfficeRuntime.storage.setItem(key, value).then(function (result) {
        return "Success: Item with key '" + key + "' saved to storage. " + value;
    }, function (error) {
        return "Error: Unable to save item with key '" + key + "' to storage. " + error;
    });
}

function CheckToken() {

    OfficeRuntime.storage.getItem("clientId").then(function (result) {

        clientId = result;

        OfficeRuntime.storage.getItem("clientSecret").then(function (result) {

            clientSecret = result;

            OfficeRuntime.storage.getItem("endpoint").then(function (result) {

                endpoint = result;

                OfficeRuntime.storage.getItem("refreshToken").then(function (result) {

                    var form = new FormData();
                    form.append("grant_type", "refresh_token");
                    form.append("client_id", clientId);
                    form.append("client_secret", clientSecret);
                    form.append("refresh_token", result);
                    form.append("platform", "excel365");
                    var endpointDomain = endpoint.substr(0, endpoint.indexOf("/", 8) + 1);

                    var settings = {
                        "url": endpointDomain + "oauth2/token",
                        "method": "POST",
                        "timeout": 0,
                        "processData": false,
                        "mimeType": "multipart/form-data",
                        "contentType": false,
                        "data": form
                    };

                    $.ajax(settings).done(function (response) {

                        const obj = JSON.parse(response);
                        $("div.debug").text(obj.access_token);
                        g_token = obj.access_token;
                        storeValue("accesstoken", obj.access_token);
                        token = obj.access_token;
                        storeValue("refreshToken", obj.refresh_token);
                        window.accessToken = obj.access_token;

                        //setCellValue("H1", obj.access_token);
                        //
                        //getCellValue("H1");

                        console.log("token = " + obj.access_token);

                        OfficeRuntime.storage.getItem("accesstoken").then(function (result) {
						    displayForm();
                        });
                    }).fail(function (error) {


                        console.log(error);
                        /*$("#LogoutButton").hide();
                        $("#LoginButton").show();
                        $("#functionDropDown").hide();
                        $(".formcontent").hide();
                        $("div.status").text("Click login and enter your credentials to get started.");*/
					
					    // If error logout user
					    OnClickLogout();
                    });
                });
            });
        });

    });
}

/** Hides the login screen and reveals the query building form.  This is used after
 *    login and token refresh 
 * 
 */
function displayForm() {
	$(".LogoutButton").show();
	$(".LoginButton").hide();
	$("#functionDropDown").show();
	$(".formcontent").show();
	$("div.introtext").html("");
	$("div.status-query").html("<p><b>To get as-filed data,</b> choose: a function from the drop-down menu below; <em>at least one search parameter</em> " 
		+ "from the list of options that appear, and; as many 'Fields to Return' as needed - then click Get.</p>");
    $("div.status-validate").html("<p>Users provisioned to validate filings can get results directly into Excel. <a href=\"https://xbrl.us/membership\" target=\"_blank\">How can I join?</a></p>");
}


function setCellValue(cell, value) {

    // Run a batch operation against the Excel object model
    Excel.run(function (ctx) {
        // Create a proxy object for the active sheet
        var sheet = ctx.workbook.worksheets.getFirst();
        // Queue a command to write the sample data to the worksheet
        sheet.getRange(cell).values = value;

        // Run the queued-up commands, and return a promise to indicate task completion
        return ctx.sync();
    }) .catch(errorHandler);
}

function getCellValue(cell) {
    Excel.run(function (context) {
        var sheet = context.workbook.worksheets.getFirst();
        var range = sheet.getRange(cell);
        range.load("values");
        return context.sync()
            .then(function () {
                console.log(JSON.stringify(range.values, null, 4));
  
            });

        
 
    }).catch(errorHandler);
}

function errorHandler(error) {
 
    if (error instanceof OfficeExtension.Error) {
        console.log("Debug info: " + JSON.stringify(error.debugInfo));
    }
}

function parse_query_string(query) {
    var vars = query.split("&");
    var query_string = {};
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        var key = decodeURIComponent(pair[0]);
        var value = decodeURIComponent(pair[1]);
        // If first entry with this name
        if (typeof query_string[key] === "undefined") {
            query_string[key] = decodeURIComponent(value);
            // If second entry with this name
        } else if (typeof query_string[key] === "string") {
            var arr = [query_string[key], decodeURIComponent(value)];
            query_string[key] = arr;
            // If third or later entry with this name
        } else {
            query_string[key].push(decodeURIComponent(value));
        }
    }
    return query_string;
}