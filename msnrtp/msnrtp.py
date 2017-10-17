''' https://msdn.microsoft.com/en-us/library/dd358336.aspx
http://stackoverflow.com/questions/3052202/how-to-analyse-contents-of-binary-serialization-stream
'''
import binascii
import struct
import packetview


OP_REQUEST = 0
OP_ONEWAYREQUEST = 1
OP_REPLY = 2


# Common types


class CountedString(object):

    def __init__(self, string_encoding, value):
        self.string_encoding = string_encoding
        self.value = value

    def pack(self):
        string_data = self.value.encode('utf-8')
        length = len(string_data)
        return struct.pack('<Bi', self.string_encoding, length) + string_data

    @classmethod
    def unpack(cls, byts):
        string_encoding, length = struct.unpack("<Bi", byts[:5])
        if string_encoding == 0:
            # TODO: 0 indicates a 'unicode' string, need to verify how to
            # pack/unpack unicode data
            raise NotImplementedError()
        if string_encoding not in [0, 1]:
            raise Exception()
        byts = byts[5:]
        string_data = byts[:length]
        return cls(string_encoding, string_data.decode('utf-8'))


# Message frame structure


class SingleMessage(object):

    protocol_id = 0x54454E2E
    major_version = 1
    minor_version = 0

    def __init__(self, operation_type, message, headers=None):
        if operation_type not in (OP_REQUEST, OP_ONEWAYREQUEST, OP_REPLY):
            raise Exception("Invalid operation type: {}".format(operation_type))
        self.operation_type = operation_type
        self.content_dist = 0
        self.length = len(message)
        self.headers = headers or []
        self.message = message

    def __repr__(self):
        return 'SingleMessage({}, {}, {})'.format(
            self.operation_type, self.length, repr(self.headers))

    def pack(self):
        data = struct.pack(
           '<iBBHHi',
           self.protocol_id,
           self.major_version,
           self.minor_version,
           self.operation_type,
           self.content_dist,
           self.length,
        )
        for header in self.headers:
            data += header.pack()
        data += struct.pack('<H', 0)
        data += self.message
        return data

    @classmethod
    def bytes_needed(cls, byts):
        preable, ibyts = byts[:14], byts[14:]
        l = struct.unpack('<iBBHHi', preable)
        assert l[0] == cls.protocol_id
        assert l[1] == cls.major_version
        assert l[2] == cls.minor_version
        operation_type = l[3]
        content_dist = l[4]
        length = l[5]
        headers = []
        while True:
            header, ibyts = cls.consume_header(ibyts)
            if header.header_token == 0:
                break

            # header_token, ibyts = ibyts[:2], ibyts[2:]
            # if header_token == '\x00\x00':
            #     break

            # TODO: Unpack headers
        needed = length - len(ibyts)
        if needed > 0:
            return needed
        return 0

    @classmethod
    def unpack(cls, byts):
        preable, ibyts = byts[:14], byts[14:]
        l = struct.unpack('<iBBHHi', preable)
        assert l[0] == cls.protocol_id
        assert l[1] == cls.major_version
        assert l[2] == cls.minor_version
        operation_type = l[3]
        content_dist = l[4]
        length = l[5]
        headers = []
        while True:
            header, ibyts = cls.consume_header(ibyts)
            if header.header_token == 0:
                break

            # header_token, ibyts = ibyts[:2], ibyts[2:]
            # if header_token == '\x00\x00':
            #     break

            # TODO: Unpack headers

        assert len(ibyts) == length, (len(ibyts), length)
        return cls(operation_type, ibyts, headers=headers)

    @classmethod
    def unpack_header(cls, byts):
        header_type, = struct.unpack('<H', byts[:2])
        return headers[header_type].unpack(byts)

    @classmethod
    def consume_header(cls, byts):
        header = cls.unpack_header(byts)
        header_data = header.pack()
        if header_data != byts[:len(header_data)]:
            raise Exception
        return header, byts[len(header_data):]


# Message Headers


class EndHeader(object):
    header_token = 0

    def pack(self):
        return struct.pack('<H', self.header_token)

    @classmethod
    def unpack(cls, byts):
        header_token, = struct.unpack(
            '<H', byts[:2]
        )
        if header_token != cls.header_token:
            raise Exception("Invalid header token or data type")
        return cls()


class StatusCodeHeader(object):
    header_token = 2
    data_type = 3  # UInt16

    def __init__(self, status_code):
        self.status_code = status_code

    def pack(self):
        return struct.pack('<HBH', self.header_token, self.data_type, self.status_code)

    @classmethod
    def unpack(cls, byts):
        header_token, data_type = struct.unpack(
            '<HB', byts[:3]
        )
        if header_token != cls.header_token or data_type != cls.data_type:
            raise Exception('Invalid header token or data type')
        status_code, = struct.unpack('<H', byts[3:5])
        return cls(status_code)


class StatusPhraseHeader(object):

    header_token = 3
    data_type = 1

    def __init__(self, value):
        self.value = value

    def pack(self):
        data = struct.pack(
            '<HB', self.header_token, self.data_type
        )
        return data + CountedString(1, self.value).pack()

    @classmethod
    def unpack(cls, byts):
        header_token, data_type = struct.unpack(
            '<HB', byts[:3]
        )
        if header_token != cls.header_token or data_type != cls.data_type:
            raise Exception("Invalid header token or data type")
        return cls(CountedString.unpack(byts[3:]).value)


class RequestUriHeader(object):

    header_token = 4
    data_type = 1

    def __init__(self, uri):
        self.string_encoding = 1
        self.uri = uri

    def pack(self):
        data = struct.pack(
            '<HB', self.header_token, self.data_type
        )
        return data + CountedString(1, self.uri).pack()

    @classmethod
    def unpack(cls, byts):
        header_token, data_type = struct.unpack(
            '<HB', byts[:3]
        )
        if header_token != cls.header_token or data_type != cls.data_type:
            raise Exception("Invalid header token or data type")
        uri_value = CountedString.unpack(byts[3:]).value
        return cls(uri_value)


class CloseConnectionHeader(object):
    header_token = 5
    data_type = 0

    def pack(self):
        return struct.pack(
            '<HB', self.header_token, self.data_type
        )

    @classmethod
    def unpack(cls, byts):
        header_token, data_type = struct.unpack(
            '<HB', byts[:3]
        )
        if header_token != cls.header_token or data_type != cls.data_type:
            raise Exception('Invalid header token or data type')
        return cls()


class ContentTypeHeader(object):

    header_token = 6
    data_type = 1

    def __init__(self, content_type):
        self.content_type = content_type

    def pack(self):
        data = struct.pack(
            '<HB', self.header_token, self.data_type
        )
        return data + CountedString(1, self.content_type).pack()

    @classmethod
    def unpack(cls, byts):
        header_token, data_type = struct.unpack(
            '<HB', byts[:3]
        )
        if header_token != cls.header_token or data_type != cls.data_type:
            raise Exception("Invalid header token or data type")
        content_type = CountedString.unpack(byts[3:]).value
        return cls(content_type)


headers = {
    EndHeader.header_token: EndHeader,
    StatusCodeHeader.header_token: StatusCodeHeader,
    StatusPhraseHeader.header_token: StatusPhraseHeader,
    ContentTypeHeader.header_token: ContentTypeHeader,
    CloseConnectionHeader.header_token: CloseConnectionHeader,
    RequestUriHeader.header_token: RequestUriHeader,
}


class RemotingRequest(object):

    def __init__(self, message, response=None):
        self.message = message
        self.response = None


class RemotingResponse(object):

    def __init__(self, request, message):
        self.request = request
        self.message = message


class RemotingMethod(object):

    def __init__(
            self, uri, serverinfo, methodname, arg_spec, return_spec,
            content_type='application/octet-stream'):
        self.uri = uri
        self.serverinfo = serverinfo
        self.methodname = methodname
        self.arg_spec = arg_spec
        self.return_spec = return_spec
        self.content_type = content_type

    def create_request(self, inputargs):
        '''
        MS-NRTP 3.1.5.1.1 Mapping Remote Method Request

        Information required to perform a Remote Method invocation consists of a
        Server Type or Server Interface name, a Remote Method name, Input
        Arguments, Generic Arguments values, Method Signature, and a Call Context.

        The implementation MAY construct an Array of System.Object classes called
        Message Properties in order to transmit implementation-specific information
        to the server. The Array, if constructed, MUST contain items whose Remoting
        Types are instances of the DictionaryEntry Class as specified in
        DictionaryEntry (section 2.2.2.6). Each DictionaryEntry item MUST contain
        the name and the value of the implementation-specific information.<33>

        The request is serialized into the serialization stream by using the
        records specified in [MS-NRBF], as follows:

        A SerializationHeaderRecord record as specified in [MS-NRBF] MUST be
        serialized. The Remote Method invocation request is serialized using a
        BinaryMethodCall record and a MethodCallArray record. The Server Type or
        the Server Interface name MUST be serialized in the TypeName field of the
        BinaryMethodCall record. The Remote Method name is serialized in the
        MethodName field of the BinaryMethodCall record. The MethodCallArray record
        is conditional and the rules for the presence of the MethodCallArray record
        are given in the following table. The table specifies the rules for
        serializing the request and the values for the MessageEnum field of the
        BinaryMethodCall record.
        '''
        from msnrbf.records import *
        from msnrbf.grammar import *
        args = []
        for n, (bspec, pspec,) in enumerate(self.arg_spec):
            if bspec == bt.STRING and pspec is None:
                args.append(
                    ValueWithCode(
                        LengthPrefixedString.enum,
                        inputargs[n],
                    )
                )
        method = BinaryMethodCall(
            MessageEnum(NoContext=True, ArgsInline=True),
            self.methodname,
            self.serverinfo,
            args=ArrayOfValueWithCode(args),
        )
        message_body = RemotingMessage.build_method_call(method)
        msg = SingleMessage(
            OP_REQUEST,
            message_body.pack(),
            headers=[
                RequestUriHeader(self.uri),
                ContentTypeHeader(self.content_type)
            ]
        )
        return msg

    def create_response(self, value=None, exception=None):
        '''
        MS-NRTP 3.1.5.1.2 Mapping Remote Method Invocation Reply
        '''
        from msnrbf.records import *
        from msnrbf.grammar import *
        method = BinaryMethodReturn(
            MessageEnum(ReturnValueInArray=True),
        )
        message_body = RemotingMessage.build_metho_return(value, exception)
        msg = SingleMessage(
            OP_REQUEST,
            message_body.pack(),
            headers=[
                RequestUriHeader(self.uri),
                ContentTypeHeader(self.content_type)
            ]
        )
        return msg
