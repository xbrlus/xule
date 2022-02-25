(function () {
    "use strict";

    var cellToHighlight;
    var messageBanner;
    var info;


    // The initialize function must be run each time a new page is loaded.
    Office.initialize = function (reason) {
        $(document).ready(function () {
            // Initialize the notification mechanism and hide it
            //var element = document.querySelector('.MessageBanner');
            //messageBanner = new components.MessageBanner(element);
            //messageBanner.hideBanner();

            $(".LogoutButton").hide();
            $(".LoginButton").show();
            $(".formcontent").hide();
            $("#functionDropDown").hide();
            $('.LoginButton').click(DoLoginDlg);
            $('.LogoutButton').click(OnClickLogout);
            $("div.status-query").html("<span class=\"login\">Click login and enter your credentials to get started.</span>");
            $("div.status-validate").html("<span class=\"login\">Click login and enter your credentials to get started.</span>");

            $('#queryPage').click(function () {
                $('#verifyPage').removeClass("selected");
                $('#queryPage').addClass("selected");
                $('#queryDiv').removeClass("hidden");
                $('#verifierDiv').addClass("hidden");
            });


            $('#verifyPage').click(function () {

                $('#verifyPage').addClass("selected");
                $('#queryPage').removeClass("selected");
                $('#queryDiv').addClass("hidden");
                $('#verifierDiv').removeClass("hidden");
            });

            //GetToken();
            CheckToken();
            


     
        });
    };
 

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

 

    function DoLoginDlg() {

        var href = window.location.href;
        var dir = href.substring(0, href.lastIndexOf('/'));

        Office.context.ui.displayDialogAsync(dir + '/Login.html?s=' + clientSecret + '&c=' + clientId, {
            height: 55, width: 30, displayInIframe: true,
            promptBeforeOpen: true
        },
            function (asyncResult) {

                var dialog = asyncResult.value;
                dialog.addEventHandler(Office.EventType.DialogMessageReceived, function (obj) {

                    try {

					
                        if (obj.message !== false && obj.message !== "False") {

                            console.log("login returned");
                            console.log(obj.message);
							
                            const words = obj.message.split('|');
                            clientSecret = words[0];
                            clientId = words[2];
                            endpoint = words[4];
                            OfficeRuntime.storage.setItem("clientId", clientId).then(function (result) {
                                OfficeRuntime.storage.setItem("clientSecret", clientSecret).then(function (result) {
                                    OfficeRuntime.storage.setItem("accesstoken", words[3]).then(function (result) {
                                        OfficeRuntime.storage.setItem("refreshToken", words[1]).then(function (result) {
                                            OfficeRuntime.storage.setItem("endpoint", endpoint).then(function (result) {
											    dialog.close();
											
											    //CheckToken();

											    window.accessToken = words[3];
											    token = words[3];
											    displayForm();
										    }, function (error) {
											    Console.log("Error: Unable to save item with key '" + key + "' to storage. " + error);
										    });
                                        }, function (error) {
                                            Console.log("Error: Unable to save item with key '" + key + "' to storage. " + error);
                                        });
                                    }, function (error) {
                                        Console.log("Error: Unable to save item with key '" + key + "' to storage. " + error);
                                    });
                                }, function (error) {
                                    Console.log("Error: Unable to save item with key '" + key + "' to storage. " + error);
                                });
                            }, function (error) {
                                Console.log("Error: Unable to save item with key '" + key + "' to storage. " + error);
                            });





                        }
                        else {

                            dialog.close();
                        }

                    }
                    catch (ex) {
                        Console.log(ex);
                        dialog.close();
                    }
                    
                });
            });
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

function OnClickLogout()
{
    storeValue("accesstoken", "");
    storeValue("refreshToken", "");
    $(".LogoutButton").hide();
    $(".LoginButton").show();
    $(".formcontent").hide();
    $("#functionDropDown").hide();
    $("div.status-query").html("<span class=\"login\">Click login and enter your credentials to get started.</span>");
    $("div.status-validate").html("<span class=\"login\">Click login and enter your credentials to get started.</span>");
}


 
doQrySheet = function (event) {
    
    Excel.run(function (ctx) {
        ctx.workbook.application.calculate('Full');
        event.completed();
        return ctx.sync();
    }).catch(function (error) {
        console.log("Error: " + error);
        if (error instanceof OfficeExtension.Error) {
            console.log("Debug info: " + JSON.stringify(error.debugInfo));
        }
    });

}; 


doQryAll = function (event) {

    Excel.run(function (ctx) {
        ctx.workbook.application.calculate('Full');
        event.completed();
        return ctx.sync();
    }).catch(function (error) {
        console.log("Error: " + error);
        if (error instanceof OfficeExtension.Error) {
            console.log("Debug info: " + JSON.stringify(error.debugInfo));
        }
    });

};

showCredentialsURL = function (event) {
    var href = 'https://xbrl.us/access-token';
    Office.context.ui.displayDialogAsync(href, {
        width: 80,
        height: 80,
        displayInIframe: false
    });
    event.completed();
};

showDocumentationURL = function (event) {
    var href = 'https://xbrlus.github.io/xbrl-api/';
    Office.context.ui.displayDialogAsync(href, {
        width: 80,
        height: 80,
        displayInIframe: false
    });
    event.completed();
};

showCommunityURL = function (event) {
    var href = 'https://xbrl.us/xbrl-api-community/';
    Office.context.ui.displayDialogAsync(href, {
        width: 80,
        height: 80,
        displayInIframe: false
    });
    event.completed();
};


