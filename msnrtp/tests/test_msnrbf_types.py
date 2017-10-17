import logging
import pytest
from msnrbf.types import (
    pack_length, unpack_length, LengthPrefixedString, Datetime, bits, frombits
)

logger = logging.getLogger(__name__)


@pytest.fixture
def lparams():
    return [
      ('\x80\x02', 256),
      ('\x86\x01', 134),
      ('\x80\x01', 128),
      ('\x7f', 127),
      ('\x40', 64),
      ('\x04', 4),
      ('\x07', 7),
    ]


def test_pack_length(lparams):
    for params in lparams:
        byts, i = params
        pakd = pack_length(i)
        if byts == pakd:
            logger.debug("%s %s pass", repr(i), repr(byts))
        else:
            logger.info("%s %s != %s fail", repr(i), repr(byts), repr(pakd))


def test_unpack_length(lparams):
    for params in lparams:
        byts, i = params
        length, n = unpack_length(byts)
        if length == i:
            logger.debug("%s %s pass", repr(byts), repr(i))
        else:
            logger.info("%s %s != %s fail", repr(byts), repr(length), repr(i))


def test_bits():
    n1 = 255
    b = bits(n1, high_bit_first=True)
    n2 = frombits(b, high_bit_first=True)
    assert n1 == n2
    b = bits(n1, high_bit_first=False)
    n2 = frombits(b, high_bit_first=False)
    assert n1 == n2


def test_length_prefixed_string():
    s = LengthPrefixedString(
        'Security.ISecurityQuery, Security.Client_v1.0.2.1, '
        'Version=1.1.870.17051, Culture=neutral, PublicKeyToken=a05d8f63989cf1d1'
    )
    assert (
        '\x86\x01Security.ISecurityQuery, Security.Client_v1.0.2.1, '
        'Version=1.1.870.17051, Culture=neutral, PublicKeyToken=a05d8f63989cf1d1'
    ) == s.pack(), repr(s.pack())


def test_datetime():
    b = '\x00\x00\xd0\x1c\xbc\xe6r\xd1'
    d = Datetime.unpack(b)
    assert d.pack() == b, "{} != {}".format(repr(d.pack()), repr(b))
