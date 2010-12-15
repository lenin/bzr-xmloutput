"""Tools for writing xml

Suggestion for this module: create a simple xml writer here and expurgate all
other modules of angle brackets entirely.
"""

import string

# Use xml_serializer to avoid duplicating the elementtree location logic
def escape_cdata(text):
    text = string.replace(text, "&", "&amp;")
    text = string.replace(text, "<", "&lt;")
    text = string.replace(text, ">", "&gt;")
    return text
