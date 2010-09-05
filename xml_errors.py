""" XMLError handling module """

from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
from bzrlib import (
    errors,
    osutils,
    trace,
    )
""")

from writer import _escape_cdata


class XMLError(errors.BzrError):
    """ A class that wraps an BzrError and 'serialize' it as xml."""
    internal_error = False

    def __init__(self, error):
        self.error = error

    def __str__(self):
        """__str__"""
        xml = '<?xml version="1.0" encoding="%s"?>' % \
                osutils.get_user_encoding()
        try:
            xml += '<error>%s</error>' % self.get_cause_xml()
        except Exception, e:
            xml += '<error><message>%s</message></error>' % \
                _escape_cdata(str(e))
        return xml

    def get_cause_xml(self):
        """return the cause as an xml string: class, dict and message"""
        s = '<class>%s</class><dict>%s</dict>' \
                '<message>%s</message>' \
                % (self.error.__class__.__name__,
                   self._get_dict_as_xml(self.error.__dict__),
                   _escape_cdata(str(self.error)))
        return s

    def _get_dict_as_xml(self, dict):
        """returns a dict as xml using <key> and <value> tags"""
        return ''.join(['<key>%s</key><value>%s</value>' % \
            (_escape_cdata(key),
            _escape_cdata(str(val))) \
                    for key, val in dict.iteritems() if val is not None])


def report_exception(exc_info, err_file):
    """ replace the default report_exception with a custom one that returns
    a xml representation of the error.

    :return: The appropriate exit code for this error.
    """
    exc_type, exc_object, exc_tb = exc_info
    # Log the full traceback to ~/.bzr.log
    trace.log_exception_quietly()
    err_file.write(str(XMLError(exc_object)))
    return errors.EXIT_ERROR


def handle_error_xml(func):
    """ a decorator that handle errors using our custom report_exception"""

    def xml_error_handling(*args, **kwargs):
        """ the wrapper"""
        try:
            return func(*args, **kwargs)
        except:
            import sys, os
            exitcode = report_exception(sys.exc_info(), sys.stderr)
            if os.environ.get('BZR_PDB'):
                print '**** entering debugger'
                import pdb
                pdb.post_mortem(sys.exc_traceback)
            return exitcode

    return xml_error_handling


