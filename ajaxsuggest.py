"""
most code taken and adapted from
  http://wiki.w4py.org/ajax_in_webware.html
and
  http://www.dynamicajax.com/fr/AJAX_Suggest_Tutorial-271_290_312.html

author: robert forkel
"""
# inherit from AjaxPage, which in turn inherits from ExamplePage
from ajaxpage import AjaxPage

MAX = 10 # only pass a limited number of suggestions

class AjaxSuggest(AjaxPage):

	def writeHeadParts(self):
		AjaxPage.writeHeadParts(self)

		# write css for the suggestion box
		self.write("""
<style type="text/css">
.close {
  color: red;
}
.suggest_link {
  background-color: #FFFFFF;
  padding: 2px 6px 2px 6px;
}
.suggest_link_over {
  background-color: #3366CC;
  padding: 2px 6px 2px 6px;
}
#suggestions {
  cursor: pointer;
  position: absolute; 
  background-color: #FFFFFF; 
  text-align: left; 
  border: 1px solid #000000;	
}
.show {
  display: block;
}
.hide {
  display: none;
}
</style>
""")
		# write javascript
		self.write("""
<script type="text/javascript" language="JavaScript">
<!--
//
// only the required portions of http://wiki.w4py.org/ajaxjavascript.html?
//

var request_count = 0;

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
        // fix for new-style action params
	openConnection(req,loc+"?_action_ajax_controller=&f="+func+additionalArguments);
    }
}

//
// handling of the suggestion box adapted from http://www.dynamicajax.com/fr/AJAX_Suggest_Tutorial-271_290_312.html
//

// the function to be associated with input control (initiates the ajax request):
function getSuggestions() {
    generic_ajax(false, 'suggest', escape(document.getElementById('query').value));
}

// the function handling the ajax response:
function handleSuggestions(res) {
    if (res.length > 0) {
        var e = document.getElementById('suggestions');
        e.innerHTML = '<div onmouseover="suggestOver(this)" onmouseout="suggestOut(this)" onclick="clearSuggestions()" class="suggest_link close">close</div>';
        for(i=0; i < res.length; i++) {
	    e.innerHTML += '<div onmouseover="suggestOver(this)" onmouseout="suggestOut(this)" onclick="setQuery(this.innerHTML)" class="suggest_link">' + res[i] + '</div>';
        }
        e.className = 'show';
    } else {
        clearSuggestions();
    }
}

function suggestOver(div_node) {
    div_node.className = div_node.className.replace('suggest_link', 'suggest_link_over');
}

function suggestOut(div_node) {
    div_node.className = div_node.className.replace('suggest_link_over', 'suggest_link');
}

function clearSuggestions() {
    var e = document.getElementById('suggestions')
    e.innerHTML = '';
    e.className = 'hide'
}

function setQuery(value) {
    document.getElementById('query').value = value;
    clearSuggestions();
}
-->
</script>
""")

	def writeContent(self):
		self.write("""\
<form method="GET" action="">
  <p>
    Start typing in some lowercase letters, and get words starting with these characters suggested:<br>
    <input type="text" name="query" id="query" onkeyup="getSuggestions();" autocomplete="off">
    <div class="hide" id="suggestions"></div>
  </p>
</form>
""")

        def ajax_allowed(self):
		"""
		register the suggest method for use with ajax
		"""
		return ['suggest']

  
	def suggest(self, prefix):
		"""
		we return a javascript function call as string

		the javascript function we want called is 'handleSuggestions' and we pass
		an array of strings starting with prefix.
		"""
		s = filter(lambda w: w.startswith(prefix), SUGGESTIONS)
		if not s:
			s = ['none']
		#
		# note: to pass more general python objects to the client side, use json,
		# e.g. using json-py's (https://sourceforge.net/projects/json-py/) JsonWriter.
		#
		return "handleSuggestions([%s]);" % ",".join(map(lambda w: "'%s'" % w, s[:MAX]))
  

from random import choice
from string import ascii_lowercase
SUGGESTIONS = []
for i in range(500):
	word = []
	for j in range(5):
		word.append(choice(ascii_lowercase))
	SUGGESTIONS.append(''.join(word))
