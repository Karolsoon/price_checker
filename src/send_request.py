import requests

from dataclasses import dataclass
from uuid import uuid4
from datetime import datetime


class Response:
    
    uuid = ...
    status_code = ...
    elapsed = ...
    content = ...
    sent_ts = ...


class RequestHandler:

    @dataclass
    class Response:
        uuid: str = None
        status_code: int = None
        elapsed: str = None
        content: str = None
        sent_ts: datetime = None


    def __init__(self, headers: dict):
        self.headers = headers
        self.uuid = uuid4()
        self.sent_ts: datetime = datetime.now()

    def send_request(self, url: str, cookie_policy) -> Response:
        with requests.Session() as sess:

            # Set cookie policy
            sess.cookies.set_policy(cookie_policy)

            # Set headers - domain specific
            sess.headers = self.headers

            # Send request and check status
            response = sess.get(url=url)
            response.raise_for_status()

            print(f"""
            *********** {url} ***********
            Status code: {response.status_code}
            Elapsed    : {response.elapsed}
            Sent       : {datetime.now()}
            """)

            self._set_response(response)
            return self.Response

    def _set_response(self, response: tuple):
        self.Response.uuid = self.uuid
        self.Response.status_code = response.status_code
        self.Response.elapsed = response.elapsed
        self.Response.content = response.content
        self.Response.sent_ts = self.sent_ts
