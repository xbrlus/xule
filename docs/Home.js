(function () {
    "use strict";

    var cellToHighlight;
    var messageBanner;
    var info;


    // The initialize function must be run each time a new page is loaded.
    Office.initialize = function (reason) {
        $(document).ready(function () {
            // Initialize the notification mechanism and hide it
            var element = document.querySelector('.MessageBanner');
            messageBanner = new components.MessageBanner(element);
            messageBanner.hideBanner();
 



            receiveTokenFromCustomFunction();
 

            // Add a click event handler for the highlight button.
            $('.LoginButton').click(OnCLickLoginButton);
            $('#Test1Button').click(OnClickTestEntitiy40);
            $('#ExeQryButton').click(OnClickExeQryButton);
            $('#testButton').click(OnClickTestButton);
            
            $('#AssertionDtlsRule81Button').click(OnClickAssertionDtlsRule81);
            $('#DetailsBalanceSheetFordButton').click(OnClickDetailsBalanceSheetFord);
            $('#DTSIDFordButton').click(OnCLickDTSIDFord);
            $('#LookupCalcsDtsIdButton').click(OnCLickLookupCalcsDtsId);
            $('#DTSIDforCatButton').click(OnCLickDTSIDforCat);

            $('#highlight-button').click(hightlightHighestValue);
        });
    };

    function OnClickTestButton() {
        var url = endpoint + "entity/report/search?fields=entity.*,report.id,entity.limit(40)";

        showData(url);
    }
    function OnCLickLoginButton() {

        var form = new FormData();
        form.append("grant_type", "password");
        form.append("client_id", clientId);
        form.append("client_secret", clientSecret);
        form.append("username", "david.tauriello@gmail.com");
        form.append("password", "Xb$2020Rl");
        form.append("platform", "excel365");

        var settings = {
            "url": "https://api.xbrl.us/oauth2/token",
            "method": "POST",
            "timeout": 0,
            "processData": false,
            "mimeType": "multipart/form-data",
            "contentType": false,
            "data": form
        };

        $.ajax(settings).done(function (response) {

            const obj = JSON.parse(response);
            $("div.token").text(obj.access_token);
            storeValue("accesstoken", obj.access_token);
            storeValue("refreshToken", obj.refresh_token);

            OfficeRuntime.storage.getItem("refreshToken").then(function (result) {

                if (result !== null) {
                    $("div.token").text(result);
                }
            });

        });


    }


    function OnClickExeQryButton() {
        //Excel.run(function (context) { 
        //    var range = context.workbook.getSelectedRange();
        //    range.load();
        //    await context.sync();
        //    var myRange = range._A;
        //    var url = range.values[0];
        //    var sheet = myRange.lastIndexOf("!") + 1;
        //    var div = myRange.lastIndexOf(":");
        //
        //    if (div === -1) {
        //        myRange = myRange.substring(sheet);
        //    }
        //    else {
        //        myRange = myRange.substring(
        //            sheet,
        //            div
        //        );
        //    }
        //
        //    if (url && url.length > 0) {
        //
        //        var startCol = myRange[0];
        //        var startRow = myRange.substring(1);
        //        startRow++;
        //        myRange = startCol + startRow;
        //        showTabularDataCell(url, myRange);
        //    }
        //});

    }
    function OnClickTestEntitiy40() {

        showTabularData(endpoint + "entity/report/search?fields=entity.*,report.id,entity.limit(40)");
    }

    function OnClickAssertionDtlsRule81() {



        showTabularData(endpoint + "assertion/search?fields=assertion.code,assertion.*,assertion.limit(100)&assertion.source=DQC&assertion.type=0081&report.creation-software=Toppan");
    }


    function OnClickDetailsBalanceSheetFord() {

        showTabularData(endpoint + "network/relationship/search?fields=network.link-name,network.id,relationship,relationship.id.sort(ASC),relationship.*&network.role-description=Balance&network.role-description-like=-%20Statement%20-&dts.id=363066");
    }


    function OnCLickDTSIDFord() {

        showTabularData(endpoint + "report/search?report.document-type=10-K&report.entity-name=Ford&report.entry-type=inline&fields=dts.id,report.accession,report.base-taxonomy,report.creation-software,report.document-type,report.entity-name,report.entry-url,report.filing-date,report.period-end");
    }

    function OnCLickLookupCalcsDtsId() {

        showTabularData(endpoint + "relationship/search?dts.id=363066&network.arcrole-uri=http%3A%2F%2Fwww.xbrl.org%2F2003%2Farcrole%2Fsummation-item&network.link-name=calculationLink&fields=network.link-name,network.id,relationship,relationship.id.sort(ASC),relationship.*");
    }

    function OnCLickDTSIDforCat() {

        showTabularData(endpoint + "report/search?report.document-type=10-K&report.entity-name=Caterpillar&report.entry-type=inline&fields=dts.id,report.accession,report.base-taxonomy,report.creation-software,report.document-type,report.entity-name,report.entry-url,report.filing-date,report.period-end");
    }





 
    function loadSampleData() {
        var values = [
            [Math.floor(Math.random() * 1000), Math.floor(Math.random() * 1000), Math.floor(Math.random() * 1000)],
            [Math.floor(Math.random() * 1000), Math.floor(Math.random() * 1000), Math.floor(Math.random() * 1000)],
            [Math.floor(Math.random() * 1000), Math.floor(Math.random() * 1000), Math.floor(Math.random() * 1000)]
        ];

        // Run a batch operation against the Excel object model
        Excel.run(function (ctx) {
            // Create a proxy object for the active sheet
            var sheet = ctx.workbook.worksheets.getActiveWorksheet();
            // Queue a command to write the sample data to the worksheet
            sheet.getRange("B3:D5").values = values;

            // Run the queued-up commands, and return a promise to indicate task completion
            return ctx.sync();
        })
            .catch(errorHandler);
    }

    function hightlightHighestValue() {
        // Run a batch operation against the Excel object model
        Excel.run(function (ctx) {
            // Create a proxy object for the selected range and load its properties
            var sourceRange = ctx.workbook.getSelectedRange().load("values, rowCount, columnCount");

            // Run the queued-up command, and return a promise to indicate task completion
            return ctx.sync()
                .then(function () {
                    var highestRow = 0;
                    var highestCol = 0;
                    var highestValue = sourceRange.values[0][0];

                    // Find the cell to highlight
                    for (var i = 0; i < sourceRange.rowCount; i++) {
                        for (var j = 0; j < sourceRange.columnCount; j++) {
                            if (!isNaN(sourceRange.values[i][j]) && sourceRange.values[i][j] > highestValue) {
                                highestRow = i;
                                highestCol = j;
                                highestValue = sourceRange.values[i][j];
                            }
                        }
                    }

                    cellToHighlight = sourceRange.getCell(highestRow, highestCol);
                    sourceRange.worksheet.getUsedRange().format.fill.clear();
                    sourceRange.worksheet.getUsedRange().format.font.bold = false;

                    // Highlight the cell
                    cellToHighlight.format.fill.color = "orange";
                    cellToHighlight.format.font.bold = true;
                })
                .then(ctx.sync);
        })
            .catch(errorHandler);
    }

    function displaySelectedCells() {
        Office.context.document.getSelectedDataAsync(Office.CoercionType.Text,
            function (result) {
                if (result.status === Office.AsyncResultStatus.Succeeded) {
                    showNotification('The selected text is:', '"' + result.value + '"');
                } else {
                    showNotification('Error', result.error.message);
                }
            });
    }

    // Helper function for treating errors
    function errorHandler(error) {
        // Always be sure to catch any accumulated errors that bubble up from the Excel.run execution
        showNotification("Error", error);
        console.log("Error: " + error);
        if (error instanceof OfficeExtension.Error) {
            console.log("Debug info: " + JSON.stringify(error.debugInfo));
        }
    }

    // Helper function for displaying notifications
    function showNotification(header, content) {
        $("#notification-header").text(header);
        $("#notification-body").text(content);
        messageBanner.showBanner();
        messageBanner.toggleExpansion();
    }

    /**
     * Read a token from storage.
     * @customfunction GETTOKEN
     */
    function receiveTokenFromCustomFunction() {

        OfficeRuntime.storage.getItem("accesstoken").then(function (result) {

            if (result !== null) {
                $("div.token").text(result);
            }
            // test this


        }, function (error) {
            showNotification("Error", error);
        });

    }

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

 
 


})();




function Add(first, second) {

    var tmp = [[1, 2, 3, 4]];

    return tmp;

   //return new OfficeExtension.Promise(function (resolve, reject) {
   //
   //    //var tmp = first * second;
   //    var tmp = [[5, 2, 3, 4]]; 
   //
   //    resolve(tmp);
   //    
   //});
    
}



