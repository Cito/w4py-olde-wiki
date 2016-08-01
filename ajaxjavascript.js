//some code based on ideas from Apple developer code (developer.apple.com) and nevow 0.4.1 (www.nevow.org)

// refactoring of existing ajax functionality to allow server-initiated data to be processed client side
// and to prevent server timeouts

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

function openConnection(req,url)
{
    if (req) {
        req.onreadystatechange = function() {
                                    if (req.readyState==4) {
                                        if (req.status == 200) {
                                            try {
                                                eval(req.responseText);
                                            } catch (e) {
                                                ; //ignore errors
                                            }
                                        }
                                    }
                                };
        req.open("GET", url, true);
        req.send(null);
    }
}

//generic ajax call
function generic_ajax(pre_action,func) {
    if (pre_action) {
        eval(pre_action);
    }
    var additionalArguments = ''
    for (i = 2; i<arguments.length; i++) {
        additionalArguments += '&a='
        additionalArguments += encodeURIComponent(arguments[i])
    }
    request_count += 1;
    additionalArguments += '&a=' + request_count;
    var loc = document.location.toString();
    if (loc.indexOf('?') != -1) {
        loc = loc.substr(0,loc.indexOf('?'));
    }
    req = createRequest();
    if (req) {
        openConnection(req,loc+"?_action_=ajax_controller&f="+func+additionalArguments);
    }
}

//ajax call specific to forms
function generic_ajax_form(func,f,dest) {
    if (dest) {
        var hf = document.getElementById(dest);
        hf.innerHTML = '<img src="images/animateddots.gif" alt="Your form is being processed. Please be patient."/>';
    }

    var values = Array();
    for (i=0; i<f.elements.length; i++) {
        var e = f.elements[i];
        name = e.name;
        if (!(((e.type == 'checkbox') || (e.type == 'radio')) && (!e.checked))) {
            values[i] = [name,e.value];
        }
    }

       
    var additionalArguments = ''
    for (i = 0; i<values.length; i++) {
        additionalArguments += '&a='
        additionalArguments += encodeURIComponent(values[i])
    }
    request_count += 1;
    additionalArguments += '&a=' + request_count;
    var loc = document.location.toString();
    if (loc.indexOf('?') != -1) {
        loc = loc.substr(0,loc.indexOf('?'));
    }
    req = createRequest();
    if (req) {
        openConnection(req,loc+"?_action_=ajax_controller&f="+func+additionalArguments);
    }
}

//below are some ajax helper functions
function ajax_setTag(which, val) {
    var e = document.getElementById(which);
    e.innerHTML = val;
}


function ajax_setClass(which, val) {
    var e = document.getElementById(which);
    e.className = val;
}

function ajax_setID(which, val) {
    var e = document.getElementById(which);
    e.id = val;
}

function ajax_setValue(which, val) {
    var e = document.getElementById(which);
    e.value = val;
}

function ajax_setReadonly(which, val) {
    var e = document.getElementById(which);
    if (val) {
        e.setAttribute('readonly','readonly');
    }
    else {
        e.removeAttribute('readonly');
    }
}
