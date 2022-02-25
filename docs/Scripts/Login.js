(Office.initialize = function (reason) {

})();

$(document).ready(function () {


    var query = window.location.search.substring(1);
    var qs = parse_query_string(query);
    var bInLogin = false;
    clientSecret = qs.s;
    clientId = qs.c;
    endpoint = "https://api.xbrl.us/";

    $("#clientSecret").val(clientSecret);
    $("#clientId").val(clientId);
    $('#LoginButton').click(OnCLickLoginButton);        
    $('#CloseButton').click(OnCloseButton);

    function OnCloseButton() {
        Office.context.ui.messageParent(false);
    }
      
    function OnCLickLoginButton() {
           
        clientSecret = $("#clientSecret").val();
        clientId = $("#clientId").val();
        GetToken($("#username").val(), $("#password").val());

    }

    function GetToken(username, password) {

        if (bInLogin) return;

        bInLogin = true;

        endpoint = $("#endpoint").val();

        var form = new FormData();
        form.append("grant_type", "password");
        form.append("client_id", clientId);
        form.append("client_secret", clientSecret);
        form.append("username", username);
        form.append("password", password);
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

            var obj = JSON.parse(response);

            var retVal = clientSecret + "|" + obj.refresh_token + "|" + clientId + "|" + obj.access_token + "|" + endpoint;

            bInLogin = false;
            if (obj.access_token) {

                $("div.loginResult").text("Login Successful");
                Office.context.ui.messageParent(retVal);
            }
            else {

                $("div.loginResult").text("Login Failed");
                    
            }

            $("div.loginDebugResult").text(response);

        }).fail(function (error) {
            $("div.loginDebugResult").text(error.message);
            $("div.loginResult").text("Login Failed");
                bInLogin = false;
        });

    }



});