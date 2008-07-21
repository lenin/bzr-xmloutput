
from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
import bzrlib
from bzrlib import (
    errors,
    debug,
    )
""")

from bzrlib.xml_serializer import _escape_cdata
from bzrlib import trace
#, errors, debug

class XMLError(errors.BzrError):
    internal_error = False

    def __init__(self, error):
        self.error = error

    def __str__(self):
        xml = '<?xml version="1.0" encoding="%s"?>' % bzrlib.user_encoding
        try:
            xml += '<error>%s</error>' % self.get_cause_xml()
        except Exception, e:
            xml += '<error><message>%s</message></error>' % \
                _escape_cdata(str(e))
        return xml
    
    def get_cause_xml(self):
        s = '<class>%s</class><dict>%s</dict>' \
                '<message>%s</message>' \
                % (self.error.__class__.__name__,
                   self._get_dict_as_xml(self.error.__dict__),
                   _escape_cdata(str(self.error)))
        return s
                   
    def _get_dict_as_xml(self, dict):
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

    def xml_error_handling(*args, **kwargs):
        #global original_report_exception
        #original_report_exception = trace.report_exception
        #trace.report_exception = report_exception
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
        #finally:
        #    trace.report_exception = original_report_exception

    return xml_error_handling


