import requests
from urllib3.util.url import parse_url

from dataclasses import dataclass
from uuid import uuid4
from datetime import datetime

from headers.cookie_policies import BlockAll


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
        content: bytes = None
        site_name: str = None
        sent_ts: datetime = None


    def __init__(self, headers: dict):
        self.headers = headers
        self.uuid = uuid4()
        self.sent_ts: datetime = datetime.utcnow()
        self.url: str = ''

    def send_request(self, url: str, cookie_policy) -> Response:
        self.url = url
        with requests.Session() as sess:

            # Set cookie policy
            sess.cookies.set_policy(cookie_policy)

            # Set headers - domain specific
            sess.headers = self.headers

            # Send request and check status
            self.sent_ts = datetime.utcnow()
            response = sess.get(url=url)
            response.raise_for_status()

            print(f"""[HTTP]\t[{datetime.utcnow()}]\t[{url}]\t[{response.status_code}]\t[{response.elapsed}]""")

            self._set_response(response)
            return self.Response

    def _set_response(self, response: tuple):
        self.Response.uuid = self.uuid
        self.Response.status_code = response.status_code
        self.Response.elapsed = response.elapsed
        self.Response.site_name = self.get_site_name()
        self.Response.content = response.content
        self.Response.sent_ts = self.sent_ts
    
    def get_content_to_file(self, url: str, filename: str, cookie_policy=BlockAll):
        response = self.send_request(url, cookie_policy=cookie_policy)
        with open(filename, mode='bw') as f:
            f.write(response.content)
    
    def get_site_name(self):
        domain = parse_url(self.url).host.split('.')
        if not domain[-2] == 'com':
            return domain[-2].upper()
        return domain[-3].upper()
