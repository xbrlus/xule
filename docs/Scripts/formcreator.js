//const client_secret = "";
//const username = "";
//const password = "";
var functionJSON;

function getBaseUrl() {
    var re = new RegExp(/^.*\//);
    return re.exec(window.location.href);
}

$(document).ready(function () {

    var jsonPath = getBaseUrl()[0] + "queries.json";
    jQuery.getJSON(jsonPath, GenerateFunctions);

    
  

});

function GenerateFunctions(json) {
    functionJSON = json;
    var id = "functionDropDown"
    var container = $("<div/>").addClass("form-input")
        .append($("<label/>", {
            "for": id
        }).append("Function"));
    $("#funcSel").empty();
    // Generate the dropdown
    var optionsList = $("<select/>", {
        "list": "function.options",
        "id": id
    });

    optionsList.append(
        $("<option/>", { "value": "" })
            .append("")  // Make sure that there is a label for the option
    );
 
    for (var elementName in json) {
 
        optionsList.append(
            $("<option/>", { "value": elementName })
                .append(elementName)  // Make sure that there is a label for the option
        );
    }


    container.append(optionsList).appendTo("#funcSel");
 
    $("#functionDropDown").change(function () {
        var func = $(this).val();
        GenerateForm(json[func]);
    });


}
 
function GenerateForm(func) {
    $("#target").empty();
    $("#SubmitDiv").empty();

    if (func == undefined) {
        return;
    }

    let form = func.ParameterLayout;
    
    // For each element in the form JSON, create the appropriate
    // HTML form part and append it to the document
    for (var elementName in form) {
        var element = form[elementName];
        // Add an ID property to the element so we can use it later
        element.id = elementName;
        console.log(element);
        if (element.type === "inputField") {
            createInputField(element);
        }
        else if (element.type === "dropDown") {
            createDropDown(element);
        }
        else if (element.type === "dropDownGeneratedFromUserEntry") {
            createDropDownFromUserEntry(element);
        }
        else if (element.type === "dropDownGeneratedFromAPI") {
            createDropDownFromAPI(element);
        }

 
    }

    // Add the checkboxto the end of the form
    
    $("<span/>")
   
        .append($("<input/>", {
            "id": "formAndData",
            "type": "radio",
            "value": "0",
            "checked": "checked",
            "name": "outputRadio"
        })).append("Function + Data").appendTo("#SubmitDiv")

    $("<span/>")   

        .append($("<input/>", {
            "id": "dataOnly",
            "type": "radio",
            "value": "1",
            "name": "outputRadio"
        })).append("Data").appendTo("#SubmitDiv")

    $("<span/>")
        .append($("<input/>", {
            "id": "pasteQuery",
            "type": "radio",
            "value": "2",
            "name": "outputRadio"
        })).append("Query")
        .appendTo("#SubmitDiv")

    // Add the checkboxto the end of the form


    // Add the submit button to the end of the form
    // TODO: This code will often be run before all of the API-related
    // inputs are generated, so it doesn't always get placed last
    $("<div/>").addClass("form-input")
        .append($("<input/>", {
            "id" : "submitButton",
            "type": "button",
            "onclick": "OnSearch();",
            "value": "Get",
            "class": "Button  Button--primary Button-label"
        }))
        .appendTo("#SubmitDiv")


  

}



function createInputField(data) {

    var defaultVal = "";
    if (data.defaultValue) {
        defaultVal = data.defaultValue;
    }

    $("<div/>").addClass("form-input")
        .append($("<label/>", {
            "for": data.id
        }).append(data.title))
        .append($("<input/>", {
            "type": "text",
            "id": data.id,
        }).val(defaultVal))
        .appendTo("#target");

    $("#" + data.id).change(function () {

        if (data.Action_Invalidates) {

            var inputval = $(this).val();

            var disable = inputval.length > 0;
            var fields = data.Action_Invalidates.split(",");
 
            for (var field in fields) {
                var input = $("#" + fields[field]);

                input.prop("disabled", disable);
                if (disable && input.is('input, textarea')) {
                    input.val("");
                }
            }
        }

    });

}

function createDropDown(data) {
    var container = $("<div/>").addClass("form-input")
        .append($("<label/>", {
            "for": data.id
        }).append(data.title));

    // Generate the dropdown
    var optionsList = $("<select/>", {
        "list": data.APIParameter + ".options",
        "id": data.id
    });

    if (data.multiSelect) {
        optionsList.attr({ "multiple": true });
    }

    container.append(optionsList).appendTo("#target");


    var retVal = createDropDownEx(data, optionsList);

    var sortable = false;

    if (data.sortable != undefined) {
        sortable = data.sortable;
    }

    if (data.isAddable) {

        var ss = new SlimSelect({
            select: "#" + data.id,
            closeOnSelect: false,
            isSortable: sortable,
            addable: function (value) {
                // Return the value string
                return value;
            }
        })
    }
    // If the dropdown is supposed to be multiselect, enable it
    else if (data.multiSelect) {
    
        var ss = new SlimSelect({
            select: "#" + data.id,
            closeOnSelect: false,
            isSortable: sortable
        })

        //container.attr({ "style": "min-height: 240px" });

    }

    return retVal;
}
function createDropDownEx(data, optionsList) {
    // If the dropdown is supposed to be multiselect, enable it
    if (data.multiSelect) {
        optionsList.attr({ "multiple": true });

    }

    let defaultVals = [];

    if (data.defaultValues) {

        defaultVals = data.defaultValues.split(",");

    }



    if (data.dropDownContent.startInteger) {

        var start = data.dropDownContent.startInteger;
        var end = data.dropDownContent.endInteger;

        if (typeof end === "string") {

            if (end.indexOf("present") >=0 ) {

                var strNdx = end.indexOf("+");

                addyears = end.substring(strNdx + 1);
                end = parseInt(new Date().getFullYear()) + parseInt(addyears);
            }
        }

        for (Ndx = start; Ndx <= end; Ndx++) {
            // For some reason, "option" is a string that represents the index,
            // not the actual substring
            

            optionsList.append(
                $("<option/>", { "value": Ndx })
                    .append(Ndx)  // Make sure that there is a label for the option
            );
        }


    }
    else {


        // Add the dropdown options
        var options = data.dropDownContent.split(",");
        for (var option in options) {
            // For some reason, "option" is a string that represents the index,
            // not the actual substring
            if (defaultVals.indexOf(options[option]) >= 0 ) {
                optionsList.append(
                    $("<option />", {
                        "value": options[option], "id": options[option], "selected": true })
                        .append(options[option])  // Make sure that there is a label for the option
                );


            }
            else {
                optionsList.append(
                    $("<option/>", { "value": options[option], "id": options[option] })
                        .append(options[option])  // Make sure that there is a label for the option
                );
            }



            
        }
    }
    

    return optionsList;
}

function createDropDownFromUserEntry(data) {
    // TODO: Since this function might be run often in a single
    // session, would it be worth attempting to cache the token
    // and only request a new one when the current one expries?

    $("<div/>").addClass("form-input")
        .append($("<label/>", {
            "for": data.id
        }).append(data.title))
        .append($("<input/>", {
            "type": "text",
            "id": data.id,
        }))
        .appendTo("#target");
 //
 //  var container = $("<div/>").addClass("form-example")
 //      .append($("<label/>", {
 //          "for": data.id
 //      }).append(data.title));

   // // Generate the dropdown
   // var optionsList = $("<select/>", {
   //     "list": data.APIParameter + ".options",
   //     "id": data.id
   // });

    var autocompInput = $("#" + data.id);
    
    $("#" + data.id).change(function () {

        if (data.Action_Invalidates) {

            var inputval = $(this).val();

            var disable = inputval.length > 0;
            var fields = data.Action_Invalidates.split(",");

            for (var field in fields) {
                var input = $("#" + fields[field]);

                input.prop("disabled", disable);
                if (disable && input.is('input, textarea') )  {
                    input.val("");
                }
            }
        }

    });

  
    autocompInput.autocomplete({
        source: function (request, response) {
            console.log(request);

            var URL = endpoint + data.APIQuery;
            URL = URL.replace("{PassedParameter}", request.term);

            var settings = {
                "url": URL,
                "method": "GET",
                "timeout": 0,
                "headers": {
                    "Authorization": "Bearer " + token
                },
            };

            $.ajax(settings).done(function (resp) {
                response($.map(resp.data, function (item) {

                    var label = "";
                    if (Array.isArray(data.dropDownContent)) {
                        data.dropDownContent.forEach(function (val) {
                            label = label + item[val];
                            label = label + ",";
                        });

                        label = trim(label, ',');
                    }
                    else {
                        label = item[data.dropDownContent];
                     
                    }

                    return {
                        label: label,
                        value: item[data.dropDownValue]
                    };
                }));
            });
        },
        select: function (event, ui) {

            if (data.Action_Invalidates) {

                var inputval = $(this).val();

                var disable = inputval.length > 0;
                var fields = data.Action_Invalidates.split(",");

                for (var field in fields) {
                    var input = $("#" + fields[field]);

                    input.prop("disabled", disable);
                    if (disable && input.is('input, textarea')) {
                        input.val("");
                    }

                }
            }

            if (data.Action_copyTo) {
                var typedVal = $(this).val();
                $("#" + data.Action_copyTo).attr("copydata", ui.item.label);
            }

            if (data.Action_AddsTo) {

                var curval = $("#" + data.Action_AddsTo).val();
                $("#" + data.Action_AddsTo).val(curval + ui.item.value + ",");
                $(autocompInput).val("");
                return false;
            }
            
        }
    }).focus(function () {

        if (data.RunOnSelect) {

            var inputval = $(this).attr("copydata");
            

            if (inputval.length > 0) {

                $(this).autocomplete("search", inputval);
            }

        }
    }).data("ui-autocomplete")._renderItem = function (ul, i) {
        // Inside of _renderItem you can use any property that exists on each item that we built
        // with $.map above */
        return $("<li></li>")
            .data("item.autocomplete", i) 
            .append("<a>" + i.label + " (" + i.value + ")</a>")
            .appendTo(ul);;
    };
   
 
}

jQuery('#some_text_box').on('input', function () {
    // do your stuff
});

function createDropDownFromAPI(data) {

    if (Array.isArray(data.APIQuery)) {

        var container = $("<div/>").addClass("form-input")
            .append($("<label/>", {
                "for": data.id
            }).append(data.title));

        // Generate the dropdown
        var dropdown = $("<select/>", {
            "list": data.APIParameter + ".options",
            "id": data.id
        });

        container.append(dropdown).appendTo("#target");

        data.APIQuery.forEach(function (val) {
            
            var reqSettings = {
                "url": endpoint + val,
                "method": "GET",
                "timeout": 0,
                "headers": {
                    "Authorization": "Bearer " + token
                }
            };

            $.ajax(reqSettings).done(function (reqResponse) {
                console.log(reqResponse);
                // Convert the specified data to a comma-separated list
                var options = [];
                for (var option in reqResponse[data.APIParameter]) {
                    options.push(option);
                }
                data.dropDownContent = options.join(",");

                // Generate a drop down using the extracted list
                createDropDownEx(data, dropdown);
            });


        });


    }
    else {
        var reqSettings = {
            "url": endpoint + data.APIQuery,
            "method": "GET",
            "timeout": 0,
            "headers": {
                "Authorization": "Bearer " + token
            }
        };

        $.ajax(reqSettings).done(function (reqResponse) {
            console.log(reqResponse);
            // Convert the specified data to a comma-separated list
            var options = [];
            for (var option in reqResponse[data.APIParameter]) {
                options.push(option);
            }
            data.dropDownContent = options.join(",");

            // Generate a drop down using the extracted list
            createDropDown(data);
        });
    }
 
  
   
}

function OnVerify() {

    console.log("OnVerify");

}
function OnSearch()  {
    var method = $("#functionDropDown").val();
    var outputType = $('input[name="outputRadio"]:checked').val();
    var apiCall = functionJSON[method];


    
    var params = apiCall.ParameterLayout;

    var Param1 = endpoint + apiCall.endPoint + "?";

    if (apiCall.endPoint.indexOf('/api/v1') >= 0)
    {
        var endpointDomain = endpoint.substr(0, endpoint.indexOf("/", 8));
        Param1 = endpointDomain + apiCall.endPoint + "?";

    }
    
    
    for (var elementName in params) {
        var element = params[elementName];

        if (elementName === "limit") {

            limit = $("#" + elementName).val();
            continue;
        }

        if (elementName === "offset") {

            offset = $("#" + elementName).val();
            continue;
        }

        value = $("#" + elementName).val();

        if (value != undefined && value.length > 0 &&  value != "null" ) {
            console.log(value);

            if (element.ActionReplaces != undefined) {

                Param1 = Param1.replace(element.ActionReplaces, value);

            }
            else {
                
                Param1 = Param1 + element.APIParameter;
                Param1 = Param1 + "=";

                console.log(Param1);
                var ssid = $("#" + elementName)[0].dataset.ssid;

                if (ssid !== undefined && element.sortable == true ) {

                    var tmp1 = $("." + ssid);
                    var tmp2 = $("." + ssid + " > .ss-values");

                    $("." + ssid).children(".ss-multi-selected").children('.ss-values').children('.ss-value').each(function (i, obj) {
                        var val = obj.childNodes[0].innerText;

                        if (obj.childNodes[1].classList.contains("selected")) {

                            val += ".sort(ASC)";
                        }
                        else if (obj.childNodes[2].classList.contains("selected")) {

                            val += ".sort(DESC)";
                        }
 
                        Param1 = Param1 + val;
                        Param1 = Param1 + ",";
                    });

                    Param1 = trim(Param1, ',');
                }
                else {
                    if (Array.isArray(value)) {
                        value.forEach(function (val) {
                            Param1 = Param1 + val;
                            Param1 = Param1 + ",";
                        });


                    }
                    else {
                        Param1 = Param1 + value;
                    }
                    Param1 = trim(Param1, ',');
                }

                if (elementName === "Fields") {
                    if (apiCall.limitObjects !== null && limit !== null) {

                        Param1 = Param1 + "," + apiCall.limitObjects + ".limit(" + limit + ")";
                    }

                    if (apiCall.offsetObjects !== null && offset !== null) {

                        Param1 = Param1 + "," + apiCall.offsetObjects + ".offset(" + offset + ")";
                    }
                }

                Param1 = Param1 + "&";
            }
            
        }

    }

    var apiCallStr = "";
    
    if (outputType === "2" ) {


        Excel.run(function (ctx) {
            // Create a proxy object for the active sheet
            var range = ctx.workbook.getSelectedRange();
            range.load();
            ctx.sync();
            // Queue a command to write the sample data to the worksheet
            range.formulas = Param1;

            // Run the queued-up commands, and return a promise to indicate task completion
            return ctx.sync();
        }).catch(errorHandler);
    }
    else if (outputType === "1") {
    
        showDataEx2(Param1, "", "", "1", true);


      
    }
    else {
        if (Param1.length > 255) {
            apiCallStr = '=XBRL.ShowData('
            var ConcatParam = 'CONCATENATE("';

            while (Param1.length > 0) {

                ConcatParam += Param1.substr(0, 255);
                Param1 = Param1.substr(255);
                if (Param1.length > 0) {
                    ConcatParam += '","';
                }
            }

            ConcatParam += '")';
            apiCallStr = apiCallStr + ConcatParam;
        }
        else {
            apiCallStr = '=XBRL.ShowData("'
            apiCallStr = apiCallStr + Param1;
            apiCallStr = apiCallStr + '"';
        }


        apiCallStr = apiCallStr + ',"", "", "1")';
        console.log(apiCallStr);

        Excel.run(function (ctx) {
            // Create a proxy object for the active sheet
            var range = ctx.workbook.getSelectedRange();
            range.load();
            ctx.sync();
            // Queue a command to write the sample data to the worksheet
            range.formulas = apiCallStr;

            // Run the queued-up commands, and return a promise to indicate task completion
            return ctx.sync();
        }).catch(errorHandler);
    }
     
} 



function trim(s, c) {
    if (c === "]") c = "\\]";
    if (c === "\\") c = "\\\\";
    return s.replace(new RegExp(
        "^[" + c + "]+|[" + c + "]+$", "g"
    ), "");
}