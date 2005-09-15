from SitePage import *

repopulate = '''
var lastValue = "";

function repopulate() {
    var search = document.getElementById("search").value.toLowerCase().split(/\s+/);
    var resultNames = new Array();
    var resultTitlesCapped = new Array();
    var resultTitles = new Array();
    var resultMimeTypes = new Array();
    var item, i, title, pos;
    for (i = 0; i < allNames.length; i++) {
        item = allNames[i];
        if (searchMatches(search, item)) {
            resultNames[resultNames.length] = item;
            title = capitalizeSearch(search, allTitles[i])
            resultTitlesCapped[resultTitlesCapped.length] = title;
            resultTitles[resultTitles.length] = allTitles[i];
            resultMimeTypes[resultMimeTypes.length] = allMimeTypes[i];
        }
    }
    var select = document.getElementById("pages");
    for (i = select.length; i >= resultNames.length; i--) {
        select.options[i] = null;
    }
    for (i = 0; i < resultNames.length; i++) {
        select.options[i] = new Option(resultTitlesCapped[i],
            resultNames[i] + "**" + resultMimeTypes[i]
            + "**" + resultTitles[i]);
    }
    if (! resultNames.length) {
        select.options[0] = new Option("No results", "");
    }
}

function searchMatches(search, term) {
    term = term.toLowerCase();
    var i;
    for (i = 0; i < search.length; i++) {
        if (term.indexOf(search[i]) == -1) {
            return false;
        }
    }
    return true;
}

function capitalizeSearch(search, term) {
    var i;
    for (i = 0; i < search.length; i++) {
        pos = term.toLowerCase().indexOf(search[i]);
        if (pos != -1) {
            term = term.substring(0, pos)
              + term.substring(pos, pos+search[i].length).toUpperCase()
              + term.substring(pos+search[i].length, term.length);
        }
    }
    return term;
}    

function research() {
    var search = document.getElementById("search").value;
    if (search != lastValue) {
        lastValue = search;
        repopulate();
    }
}

function getSelected() {
    var select = document.getElementById("pages");
    var items = select.options[select.selectedIndex].value.split("**");
    return items;
}

function callParent(func_name) {
    var items = getSelected();
    //window.alert("Calling " + func_name + " of " + window.opener
    //+ " which is " + window.opener[func_name]);
    window.opener[func_name](items[0], items[1], items[2]);
}

function callParentBare(func_name) {
    var search = document.getElementById("search").value;
    var name = search.toLowerCase();
    name = name.replace(/[^a-z]/g, "");
    window.opener[func_name](name, "text/html", search);
}
'''

class quickfind(SitePage):

    def awake(self, trans):
        SitePage.awake(self, trans)
        self.suppressFooter = True
        self.callParent = self.request().field('callParent', '')

    def title(self):
        return 'Quick Page Find'

    def writeArray(self, name, array):
        self.write('var %s = new Array(\n' % name)
        self.write(',\n  '.join(
            [repr(str(v)) for v in array]))
        self.write(');\n')

    def writeContent(self):
        onSelect = None
        if self.callParent:
            onSelect = 'callParent(%s); window.close();' \
                       % repr(self.callParent)
        if onSelect:
            selectAttr = ' onChange="%s"' % onSelect
        else:
            selectAttr = ''

        onCreate = "callParentBare(%s); window.close();" \
                   % repr(self.callParent)
        
        self.write('''
        <p>All pages on system:</p>
        Search:<br>
        <input type="text" id="search" size=20 onKeyUp="research()">
        <input type="button" value="clear"
         onClick="document.getElementById('search').value=''; research()">
        <input type="button" value="create"
         title="create a new wiki page by the given name"
         onClick="%s">
        <br>
        <select id="pages" size=20 style="width: 60%%"%s>
        </select><br>
        <input type="button" value="cancel (close)"
         onClick="window.close()">
        ''' % (onCreate, selectAttr))

        self.write('<script type="text/javascript">\n')
        allPages = self.wiki.allPages()
        self.writeArray('allNames', [p.name for p in allPages])
        self.writeArray('allTitles', [p.title for p in allPages])
        self.writeArray('allMimeTypes', [p.mimeType for p in allPages])
        self.write(repopulate)
        self.write('''
        lastValue = null;
        research();
        document.getElementById("search").focus();
        ''')
        self.write('\n</script>')
