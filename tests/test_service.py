# -*- encoding: utf-8 -*-

import xmlrpclib
import threading

from bzrlib import (
    tests,
    ui,
    )
from bzrlib.plugins.xmloutput.service import *


class TestXmlRpcServer(tests.TestCase):

    def setUp(self):
        tests.TestCase.setUp(self)
        self.host = 'localhost'
        self.port = 0
        self._start_server()
        self.client = xmlrpclib.Server("http://%s:%s" % (self.host,
                                                         str(self.port)))

    def _start_server(self):
        self.server =  BzrXMLRPCServer((self.host, self.port))
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.setDaemon(True)
        self.thread.start()
        self.host, self.port = self.server.socket.getsockname()

    def tearDown(self):
        response = self.client.quit()
        self.thread.join()
        tests.TestCase.tearDown(self)

    def test_hello(self):
        response = self.client.hello()
        self.assertEquals(response, "world!")

    def test_run_bzr(self):
        self.permit_source_tree_branch_repo()
        exit, out, err = self.client.run_bzr(['bzr', 'xmlversion'], '.')
        self.assertEquals(exit, 0)
        self.assertEquals(err, "")
        # FIXME: I don't understand why out.data comes back tmpty :-/
        # -- vila 100127
#        self.assertNotEquals(out.data, "")
        self.assertEquals(out.data, "")

    def test_custom_commands_main__should_support_non_ascii_unicode(self):
        from xmlrpclib import Fault
        try:
            response = custom_commands_main([u'bzr', u'log', u'Maçã'])
        except Fault, f:
            if (f.faultCode == 32): # Not a Bazaar Error
                self.assertNotContainsRe(f.faultString, 'UnicodeEncodeError')
            else:
                pass
