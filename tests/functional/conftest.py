import pytest
import redis
import requests

from pytest_dockerc import Wait, Context


class SpotContext(Context):
    @property
    def url(self):
        addr = self.container_addr("spot")
        port = self.container_port("spot")
        return f"http://{addr}:{port}"

    def wait_for_running_state(self):
        Wait(ignored_exns=(requests.ConnectionError,))(lambda: requests.get(self.url))


@pytest.fixture(scope="session")
def ctx(dockerc, dockerc_logs):
    context = SpotContext(dockerc)
    context.wait_for_running_state()
    yield context


@pytest.fixture
def redisdb(ctx):
    """ purge the db
    """
    db = redis.Redis(ctx.container_addr("redis"))
    for key in db.keys():
        db.delete(key)
    yield db
