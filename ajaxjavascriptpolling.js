// ajax support for long running requests from client to server or out-of-band requests from server to client

var server_response;
var dying = false;
var request_count = 0;


// declared in ajax.js, but put it here, too to make sure we have it
function createRequest()
{
    var req;
    if (window.XMLHttpRequest) {
        req = new XMLHttpRequest();
    } else if (window.ActiveXObject) {
        req = new ActiveXObject("Microsoft.XMLHTTP");
    }
    return req;
}


function openResponseConnection(count)
{
    if (!server_response) {
        server_response = createRequest();
    }
    if (server_response) {
        server_response.onreadystatechange = processResponse;
        var loc = document.location.toString();
        if (loc.indexOf('?') != -1) {
            loc = loc.substr(0,loc.indexOf('?'));
        }
        server_response.open("GET", loc+"?_action_=ajax_response&req_count="+count.toString(), true);
        server_response.send(null);
    }
}

function processResponse()
{
    var wait = (3 + Math.random() * 5); // 3 - 8 seconds
    if (server_response.readyState == 4) {
        if (server_response.status == 200) {
            try {
                eval(server_response.responseText);
            } catch(e) {
                ; // ignore errors
            }
            if (!dying) {
                request_count += 1;
                setTimeout("openResponseConnection(request_count)",wait*1000); // reopen the response connection
            }
        }
    }
}

function shutdown()
{
    if (server_response) {
        server_response.abort();
    }
    dying = true;
}

var userAgent = navigator.userAgent.toLowerCase()
if (userAgent.indexOf("msie") != -1) {
    /* IE specific stuff */
    /* Abort last request so we don't 'leak' connections */
    window.attachEvent("onbeforeunload", shutdown )
    /* Set unload flag */
} else if (document.implementation && document.implementation.createDocument) {
    /* Mozilla specific stuff (onbeforeunload is in v1.7+ only) */
    window.addEventListener("beforeunload", shutdown, false)
}

// open initial connection back to server
openResponseConnection(request_count);
