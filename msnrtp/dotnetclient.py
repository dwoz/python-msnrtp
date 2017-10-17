import binascii
import struct
import socket
import select
import time
import packetview
import logging
import urlparse

from msnrtp import *
from msnrbf import *
from remoting_types import *


logger = logging.getLogger()


class TimeoutException(Exception):
    pass


def address(urlstr):
    'return host/port combo'
    uprs = urlparse.urlparse(urlstr)
    port = None
    if ':' in uprs.netloc:
        host, port = uprs.netloc.split(':')
        port = int(port)
    else:
        host = uprs.netloc
    return host, port


class BasicClient(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.sock.connect((self.host, self.port))
        self.sock.setblocking(0)

    def send(self, msg):
        if hasattr(msg, 'pack'):
            msg = msg.pack()
        logger.info("sending %s bytes", len(msg))
        self.sock.send(msg)

    def recv(self):
        resp = self._recv(1024)
        while True:
            n = SingleMessage.bytes_needed(resp)
            if n == 0:
                break
            # print("get more bytes {}".format(n))
            resp += self._recv(n)
        return resp

    def _recv(self, length=0):
        self.wait_for_socket()
        return self.sock.recv(length)

    def wait_for_socket(self, timeout=30):
        start = time.time()
        while True:
            readable, writeable, exceptional = select.select([self.sock], [], [])
            if readable == [self.sock]:
                return True
            if time.time() - start > timeout:
                raise TimeoutException


def ppenum(enum):
    print(enum.ArgsInArray)


def print_node(node, name='', idt=0):
    if isinstance(node, BinaryMethodReturn):
        ppenum(node.message_enum)
    namepart = ''
    if name:
        namepart = '{}: '.format(name)
    print("*{} {}{}".format("    " * idt, namepart, node))
    try:
        children = iter(node)
    except TypeError:
        return
    if isinstance(node, stream.Class):
        print("library: {}".format(node.meta.library_name))
        for b in children:
            print_node(node[b], b, idt+1)
    elif isinstance(node, stream.Array):
        for n, b in enumerate(children):
            print_node(b, str(n), idt+1)


def test_server(server, args):
    message = server.method.create_request(args)
    addr = address(server.method.uri)
    print('Server address: {} {}'.format(*addr))
    client = BasicClient(*addr)
    client.connect()
    client.send(message.pack())
    resp = client.recv()
    msg = SingleMessage.unpack(resp)
    rm = RemotingMessage.unpack(msg.message)
    for a in rm.stream():
        print(a)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    main()
