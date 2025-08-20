import os, time, pytest
from .conftest import load_production_client

pytestmark = pytest.mark.live_usenet

def test_live_newshosting_sample():
    # Env (must exist; validated by conftest.py)
    host = os.environ["NNTP_HOST"]
    port = int(os.environ["NNTP_PORT"])
    user = os.environ["NNTP_USERNAME"]
    pwd  = os.environ["NNTP_PASSWORD"]
    group = "alt.binaries.test"
    timeout = int(os.environ.get("NNTP_TIMEOUT_SECS","30"))
    ua = os.environ.get("NNTP_USER_AGENT","YourTool/1.0")

    # Load your production NNTP client (must import pynntp as nntp)
    Client = load_production_client()

    # The client API MUST be real and call live NNTP:
    # Expected methods: connect() -> context manager, group(name), overview(start,last), body(id)
    client = Client(
        host=host,
        port=port,
        username=user,
        password=pwd,
        ssl=True,                  # enforced
        timeout=timeout,
        user_agent=ua,
    )

    with client.connect() as n:
        meta = n.group(group)     # returns dict or tuple
        if isinstance(meta, dict):
            count = int(meta.get("count", 0)); first = int(meta.get("first", 0)); last = int(meta.get("last", 0))
        else:
            # assume tuple like (resp, count, first, last, name) or (count, first, last, name)
            count = int(meta[1]); first = int(meta[2]); last = int(meta[3])
        assert count > 10, f"Group appears empty: {count}"

        start = max(last - 50, first)
        over = n.overview(start, last)  # MUST call XOVER/HDR live
        assert over, "Empty overview from live server"

        fetched = 0
        # over may be dict-like {artnum: headers}
        for artnum in list(over.keys())[:3]:
            body = n.body(artnum)  # MUST call BODY/ARTICLE live
            assert body, f"Empty body for article {artnum}"
            fetched += 1
            time.sleep(0.2)  # polite throttle
        assert fetched >= 2