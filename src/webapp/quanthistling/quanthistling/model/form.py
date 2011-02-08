import formencode
from formencode import validators, htmlfill

def custom_formatter(error):
    return '<span class="errormessage">%s</span>\n' % (htmlfill.html_quote(error))
        
class SearchForm(formencode.Schema):
    allow_extra_fields = True
    #filter_extra_fields = True
    fullentry = validators.UnicodeString(strip=True)
    head = validators.UnicodeString(strip=True)
    searchinbooks = validators.Set(not_empty=True)
    searchinbooks = validators.MinLength(1)
    logic = validators.OneOf(['AND', 'OR'])