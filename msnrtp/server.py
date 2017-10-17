import logging
import socket
from concurrent.futures import ThreadPoolExecutor
from msnrtp import SingleMessage, OP_REPLY
from msnrbf.records import BinaryMethodCall
from msnrbf.grammar import RemotingMessage
import packetview
from system_classes import RemotingException
from msnrbf.records import (
    ArraySingleObject, SerializationHeader, MessageEnd, BinaryMethodReturn
)
from msnrbf.structures import ArrayInfo
from msnrbf.enum.message_enum import MessageEnum


logger = logging.getLogger()


class Server(object):
    _max_workers = 2
    _listen_queue = 1

    def __init__(self, _sock=None, _executor=None):
        self.sock = _sock
        if _executor:
            self.executor = _executor
        else:
            self.executor = ThreadPoolExecutor(max_workers=self._max_workers)

    def run(self, addr, port):
        '''
        Listen for tcp connections.
        '''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((addr, port))
        self.sock.listen(self._listen_queue)
        futures = []
        while True:
            conn, addr = self.sock.accept()
            logger.debug("connection from: %s", addr)
            f = self.executor.submit(self.client_future, conn, addr)
            for future in futures:
                if f.done():
                    try:
                        f.result()
                    except:
                        logger.exception('Exception in future')

    def client_future(self, conn, addr):
        try:
            self.handle_client_connection(conn, addr)
        finally:
            logger.debug('clossing connection from: %s', addr)
            conn.close()

    def handle_client_connection(self, conn, addr):
        '''
        Read all the data from an incomming connection, then run the request
        handler in a threaded future.
        '''
        data = conn.recv(1024)
        if not data:
            return
        needed = SingleMessage.bytes_needed(data)
        while needed > 0:
            logger.info('need more bytes: {}'.format(d))
            chunk = conn.recv(needed)
            needed = needed - len(chunk)
            data += chunk
        packetview.view(data)
        logger.info("Received %d bytes", len(data))
        self.handle_request(conn, data)

    def handle_request(self, conn, data):
        '''
        Handle a request.
        '''
        logger.info("Handle request: %s", repr(data[:1024]))
        msg = SingleMessage.unpack(data)
        rm = RemotingMessage.unpack(msg.message)
        if isinstance(rm.method.method, BinaryMethodCall):
                request = rm.metho.method
        if not request:
            logger.info("No method found in request")
            return self.error_reply(conn, data)
        logger.info("Found request: %s", request)
        try:
            self.dispatch_request(conn, data, request)
        except Exception as e:
            logger.exception("exception while handling request")
            self.error_reply(conn, data)
            return
        # conn.sendall('\x00' * 1024)

    def dispatch_request(self, conn, data, request):
        raise Exception

    def error_reply(self, conn, data):
        try:
            logger.info("Send error response")
            rm = RemotingMessage.build_method_return(exception=RemotingException())
            conn.sendall(rm.pack())
        except:
            logger.exception("Exception durring error handling")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(message)s')
    server = Server()
    server.run('0.0.0.0', 7431)
