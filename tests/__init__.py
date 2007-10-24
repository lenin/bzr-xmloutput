# Copyright (C) 2005, 2006, 2007 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


"""Black-box tests for xmloutput plugin."""

import sys

from bzrlib.tests import (
                          adapt_modules,
                          TestCaseWithTransport,
                          TestSuite,
                          TestLoader,
                          iter_suite_tests,
                          )
from bzrlib.symbol_versioning import (
    deprecated_method,
    zero_eighteen,
    )
import bzrlib.ui as ui


def test_suite():
    testmod_names = [
                     'test_version_xml',
                     'test_status_xml',
                     'test_log_xml',
                     'test_annotate_xml',
                     'test_info_xml',
                     ]
    
    loader = TestLoader()
#    suite = loader.loadTestsFromModuleNames(testmod_names) 
    suite = loader.loadTestsFromModuleNames(["%s.%s" % (__name__, i) for i in testmod_names])

    return suite


class ExternalBase(TestCaseWithTransport):

    @deprecated_method(zero_eighteen)
    def runbzr(self, args, retcode=0):
        if isinstance(args, basestring):
            args = args.split()
        return self.run_bzr(args, retcode=retcode)

    def check_output(self, output, *args):
        """Verify that the expected output matches what bzr says.

        The output is supplied first, so that you can supply a variable
        number of arguments to bzr.
        """
        self.assertEquals(self.run_bzr(*args)[0], output)
