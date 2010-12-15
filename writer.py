"""Tools for writing xml

Suggestion for this module: create a simple xml writer here and expurgate all
other modules of angle brackets entirely.
"""

def _escape_cdata(text):
    """Escape special characters in cdata.

    :note: This does not care about the input encoding, and supports
        both unicode and byte strings.
    """
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text
