
import xmlrpclib
import threading

from bzrlib.plugins.xmloutput.service import *
from bzrlib import tests


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
        exit, out, err = self.client.run_bzr(['bzr', 'xmlversion'], '.')
        self.assertEquals(exit, 0)
        self.assertEquals(err, "")
        self.assertNotEquals(out.data, "")
        #self.assertEquals(out.data, "")

