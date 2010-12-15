"""Tools for writing xml

Suggestion for this module: create a simple xml writer here and expurgate all
other modules of angle brackets entirely.
"""

import bzrlib.xml_serializer

# Use xml_serializer to avoid duplicating the elementtree location logic
def escape_cdata(text):
    return bzrlib.xml_serializer.elementtree.ElementTree._escape_cdata(text, "utf-8")
