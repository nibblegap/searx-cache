import requests


class DataReq(dict):
    def __init__(self, **kwargs):
        self["category"] = kwargs.get("category", "general")
        self["language"] = kwargs.get("language", "en-US")
        self["q"] = kwargs.get("q", "lequipe.fr")
        self["time_range"] = kwargs.get("time_range", "")
        self["output"] = kwargs.get("output", "json")


def test_index(ctx, redisdb):
    """ Test the main endpoint to ensure that some results are returned
    """
    res = requests.post(ctx.url)
    assert res.status_code == 200

    res = requests.post(ctx.url, data={"output": "json"})
    assert res.status_code == 204

    data = DataReq()
    res = requests.post(ctx.url, data=data)
    assert res.status_code == 200

    response = res.json()
    assert len(response["results"]) > 5
    assert len(response["image_results"]) == 5
    assert len(response['videos_results']) == 2


def test_config(ctx):
    res = requests.get(ctx.url + "/config")
    assert res.status_code == 200
    assert res.json()["instance_name"] == "/e/ spot"
