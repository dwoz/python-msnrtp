import os
import pytest


TESTDIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def datadir():
    return os.path.join(TESTDIR, 'data')
