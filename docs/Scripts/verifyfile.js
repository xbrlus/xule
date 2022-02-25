
$(document).ready(function () {

    $("#verifyStatus").html("<span style='font-size:80%'><b>NOTE:</b> If a processing message does not appear below the "
    + "<em>Check Filing</em> button after it is clicked, logout and login to refresh your connection.</span>");

    $("#verifyButton").click(async function () {
        console.log(jQuery(this).val());


        var form = new FormData();

        if ($("#verifySelect")[0].files != undefined && $("#verifySelect")[0].files.length > 0) {
            form.append("file", $("#verifySelect")[0].files[0]);
        }
        else {

            var url = $("#fileURL").val();
           // let blob = await fetch(url).then(r => r.blob());
            form.append("file", url);            
        }

        form.append("format", "json");
        form.append("efm", "");
        form.append("Task", $('select[name="taskVerify"]').val());
        form.append("run_rules", $('input[name="singleVerify"]').val().trim());      
        form.append("status", $('input[name="proposedVerify"]').val());
        var settings = {
            "url": endpoint + "assertion/validate",
            "method": "POST",
            "timeout": 0,
            "processData": false,
            "headers": {
                "Authorization": "Bearer " + token
            },
            "mimeType": "multipart/form-data",
            "contentType": false,
            "data": form
        };

        $("#verifyStatus").html("<b><em>Processing file</em> - do not switch to Query until this status changes.</b>");

        $.ajax(settings).done(function (response) {

            const obj = JSON.parse(response);

            console.log(obj);
            var disp = [["CIK", "Effective Date", "Code", "Status", "Severity", "Message", "Line", "URL"]]

            if (obj.results !== undefined) {

                var info = obj.results["xucc:submission"]["xucc:info"]["@rules_version"];

                if (info != "Unknown") {

                    var cik = obj.results["xucc:submission"]["xucc:entity"]["@cik"];
                    var tax = obj.results["xucc:submission"]["xucc:info"]["@taxonomy_version"];
					var errors = obj.results["xucc:submission"]["xucc:stats"]["@num_errors"];
					
                    if (obj.results["vm:validationMessages"]["vm:validationMessage"] !== undefined) {
                        if (Array.isArray(obj.results["vm:validationMessages"]["vm:validationMessage"])) {
                            obj.results["vm:validationMessages"]["vm:validationMessage"].forEach(function (row) {


                                var newrow = [cik,
                                    row["@effectiveDate"],
                                    row["@errorCode"],
                                    row["@status"],
                                    row["@severity"],
                                    row["vm:messageDetail"],
                                    row["@lineNumber"],
                                    row["@url"]];

                                disp.push(newrow);

                            });
                        } else {
                            var row = obj.results["vm:validationMessages"]["vm:validationMessage"];
                            var newrow = [cik,
                                row["@effectiveDate"],
                                row["@errorCode"],
                                row["@status"],
                                row["@severity"],
                                row["vm:messageDetail"],
                                row["@lineNumber"],
                                row["@url"]];

                            disp.push(newrow);

                        }
                    } 
                    else {
                        disp = [["No results returned."]] ;
                    }
                    //$("#verifyStatus").text("File type: " + info);
                }
                else {
                    disp = [["Invalid XBRL .zip file for these checks."]];
                }
            }
            else {
                disp = [["Contact secfiler@xbrl.us to have your account provisioned."]];
            }

            $("#verifyStatus").html("This filing created with a <b>" + tax + " taxonomy</b> for <br /><b>CIK " + cik + "</b> has <b>" + errors + " errors</b>.<br />See details in the spreadsheet.");
		
            
            Excel.run(function (ctx) {
                // Create a proxy object for the active sheet
                var range = ctx.workbook.getSelectedRange();
                range.load();
                ctx.sync();
            
                //var results = [disp];
            
            
                let newrange = range.getResizedRange(disp.length - 1, disp[0].length - 1);
            
                // Queue a command to write the sample data to the worksheet
                newrange.values = disp;
                newrange.format.autofitColumns();
                
                // Run the queued-up commands, and return a promise to indicate task completion
                return ctx.sync();
            }).catch(errorHandler);

        }).fail(function (error) {


            console.log(error);
            $("#verifyStatus").text(error.responseText);

        });
    });


});