
import xmlrpclib
import socket
import threading

from bzrlib.plugins.xmloutput.service import *
from bzrlib import tests
from bzrlib import transport
import os, sys


class XMLRPCServer(transport.Server):
    """A test server for http transports.

    Subclasses can provide a specific request handler.
    """

    # used to form the url that connects to this server
    _url_protocol = 'http'

    def __init__(self, protocol_version=None):
        """Constructor.

        :param protocol_version: if specified, will override the protocol
            version of the request handler.
        """
        transport.Server.__init__(self)
        self.protocol_version = protocol_version
        # Allows tests to verify number of GET requests issued
        self.GET_request_nb = 0
        self._xmlrpcd = None
        self.host = 'localhost'
        self.port = 0

    def _get_xmlrpcd(self):
        if self._xmlrpcd is None:
            self._xmlrpcd =  BzrXMLRPCServer((self.host, self.port))
            register_functions(self._xmlrpcd)
            host, self.port = self._xmlrpcd.socket.getsockname()
        return self._xmlrpcd

    def _xmlrpc_start(self):
        """Server thread main entry point. """
        self._xmlrpc_running = False
        try:
            try:
                xmlrpcd = self._get_xmlrpcd()
                self._xmlrpc_base_url = 'http://%s:%s/' % (self.host, self.port)
                self._xmlrpc_running = True
            except:
                # Whatever goes wrong, we save the exception for the main
                # thread. Note that since we are running in a thread, no signal
                # can be received, so we don't care about KeyboardInterrupt.
                self._xmlrpc_exception = sys.exc_info()
        finally:
            # Release the lock or the main thread will block and the whole
            # process will hang.
            self._xmlrpc_starting.release()

        # From now on, exceptions are taken care of by the
        # SocketServer.BaseServer or the request handler.
        while self._xmlrpc_running:
            try:
                # Really an HTTP connection but the python framework is generic
                # and call them requests
                xmlrpcd.handle_request()
            except socket.timeout:
                pass

    def log(self, format, *args):
        """Capture Server log output."""
        self.logs.append(format % args)

    def setUp(self, backing_transport_server=None):
        """See bzrlib.transport.Server.setUp.

        :param backing_transport_server: The transport that requests over this
            protocol should be forwarded to. Note that this is currently not
            supported for HTTP.
        """
        if getattr(self, '_xmlrpc_running', False):
            return
        # XXX: TODO: make the server back onto vfs_server rather than local
        # disk.
        if not (backing_transport_server is None or \
                isinstance(backing_transport_server, local.LocalURLServer)):
            raise AssertionError(
                "HTTPServer currently assumes local transport, got %s" % \
                backing_transport_server)
        self._home_dir = os.getcwdu()
        self._local_path_parts = self._home_dir.split(os.path.sep)
        self._http_base_url = None

        # Create the server thread
        self._xmlrpc_starting = threading.Lock()
        self._xmlrpc_starting.acquire()
        self._xmlrpc_thread = threading.Thread(target=self._xmlrpc_start)
        self._xmlrpc_thread.setDaemon(True)
        self._xmlrpc_exception = None
        self._xmlrpc_thread.start()

        # Wait for the server thread to start (i.e release the lock)
        self._xmlrpc_starting.acquire()

        if self._xmlrpc_exception is not None:
            # Something went wrong during server start
            exc_class, exc_value, exc_tb = self._xmlrpc_exception
            raise exc_class, exc_value, exc_tb
        self._xmlrpc_starting.release()
        self.logs = []

    def tearDown(self):
        """See bzrlib.transport.Server.tearDown."""
        self._xmlrpcd.shutdown()
        self._xmlrpc_running = False
        # We don't need to 'self._http_thread.join()' here since the thread is
        # a daemonic one and will be garbage collected anyway. Joining just
        # slows us down for no added benefit.

class TestXmlRpcServer(tests.TestCase):

    server = None

    def setUp(self):
        tests.TestCase.setUp(self)
        if self.server is None:
            self.server = XMLRPCServer()
            self.server.setUp()
            self.addCleanup(self.server.tearDown)
        self.client = xmlrpclib.Server("http://%s:%s" % (self.server.host,
                                                         str(self.server.port)))

    def test_hello(self):
        response = self.client.hello()
        self.assertEquals(response, "world!")

    def test_run_bzr(self):
        exit, out, err = self.client.run_bzr(['bzr', 'xmlversion'], '.')
        self.assertEquals(exit, 0)
        self.assertNotEquals(out, "")
        self.assertEquals(err, "")
        #self.assertEquals(out, "")

