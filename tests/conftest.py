import pytest

from xdm.application import XDM


@pytest.yield_fixture
def xdm():
    yield XDM(
        debug=True,
        config_path='/tmp/xdm_test'
    )
