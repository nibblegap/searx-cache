import pytest
import redis
import requests

from pytest_dockerc import Wait, Context


class SpotContext(Context):
    @property
    def url(self):
        addr = self.container_addr("nginx")
        port = self.container_port("nginx")
        return f"http://{addr}:{port}"

    def wait_for_running_state(self):
        spot_url = "http://{}:{}".format(self.container_addr("spot"), self.container_port("spot"))
        Wait(ignored_exns=(requests.ConnectionError,), timeout=60)(
            lambda: requests.get(spot_url)
        )
        Wait(ignored_exns=(requests.ConnectionError,), timeout=60)(
            lambda: requests.get(self.url)
        )


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
