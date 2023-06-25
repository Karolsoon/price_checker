from src.send_request import RequestHandler
from headers.cookie_policies import BlockAll
from src.parsers import SinsayParser, BaseParser
from src.db_conn import LinksDatabase
from src.notifications import Notification
from headers.default import DEFAULT_HEADERS


import asyncio, aiohttp
from datetime import datetime, timedelta
from time import sleep
from random import randint
from sqlite3 import OperationalError
from requests.exceptions import HTTPError


class PriceController:

    default_headers = DEFAULT_HEADERS
    retry_count = 3

    def __init__(self, parser: BaseParser, request_handler: RequestHandler, db: LinksDatabase):
        self.parser: BaseParser = parser
        self.request_handler: RequestHandler = request_handler
        self.db: LinksDatabase = db()

    def run(self):
        links_todo = self.get_links_to_check()
        if links_todo:
            for shop_id, url_list in links_todo.items():
                headers = self.db.get_headers(shop_id)
                for full_url, link_id in url_list:
                    try:
                        complete_data = self.get_product_data(full_url, headers)
                        self.db.add_price(complete_data, link_id)
                        self.notify_if_change_in_price(link_id)
                        print(f'[RUN]\t[{datetime.utcnow()}]\t ALL OK')
                    except OperationalError as exc:
                        self._write_exception(exc, full_url)
                        print(f'[RUN]\t[{datetime.utcnow()}]\t FAILED - DB is busy!')
                    except HTTPError as exc:
                        self._write_exception(exc, full_url)
                        print(f'[RUN]\t[{datetime.utcnow()}]\t FAILED - HTTP ERROR!')
                        if exc.response.status_code == 404:
                            self.deactivate_link(link_id=link_id)
                    finally:
                        sleep(self._random_interval())

            print(f'[RUN]\t[{datetime.utcnow()}]\t Finished. Sleepy time.')
        else:
            print(f'[RUN]\t[{datetime.utcnow()}]\t Nothing to do. Sleep.')

        sleep(900)

    def add_new_link(self, full_url: str, price_alert_treshold: int=None,
                     headers: dict=None):
        headers = headers if headers else self.default_headers
        complete_data = self.get_product_data(full_url, self.default_headers)
        complete_data['price_alert_treshold'] = (
            price_alert_treshold
            if price_alert_treshold
            else int(float(complete_data['current_price']) * 0.5)
        )
        link_id = self.db.add_link(complete_data, self.default_headers)
        self.db.add_price(complete_data, link_id)

    def get_links_to_check(self) -> dict[str]:
        for _ in range(self.retry_count):
            try:
                print(f'[LOG]\t[{datetime.utcnow()}]\t Getting links to check.')
                links_by_shops = {}
                for link_id ,shop_id, full_url in self.db.get_links_for_cycle():
                    if not links_by_shops.get(shop_id, []):
                        links_by_shops[shop_id] = [(full_url, link_id)]
                    else:
                        links_by_shops[shop_id].append((full_url, link_id))
                        
                total_link_count = sum([len(x) for x in links_by_shops.values()])
                print(f'[LOG]\t[{datetime.utcnow()}]\t Got {total_link_count}')
                return links_by_shops
            except OperationalError:
                print(f'[LOG]\t[{datetime.utcnow()}]\t Failed to get links to check')
        raise RuntimeError("Couldn't fetch links for cycle. Database busy? Bad SQL?")

    def get_product_data(self, full_url: str, headers: dict) -> dict[str]:
        print(f'[LOG]\t[{datetime.utcnow()}]\t Getting {full_url}')
        request_handler = self.request_handler(headers)
        response = request_handler.send_request(full_url, cookie_policy=BlockAll)
        data = self.parser(response.content).get()
        print(f'[LOG]\t[{datetime.utcnow()}]\t OK')
        return self._format(data, response, full_url)

    def notify_if_change_in_price(self, link_id):
        # url, price, shop_name, item_name
        records = self.db.get_recent_data_by_link(link_id)
        current, previous = records
        if len(records) == 1 or current[1] >= previous[1]:
            print(f'[LOG]\t[{datetime.utcnow()}]\t No change in price')
            return False
        
        print(f'[LOG]\t[{datetime.utcnow()}]\t Price change!')
        data = {
            'old_price': previous[1],
            'new_price': current[1],
            'full_url': current[0]
        }
        notif_dict = Notification.send_text(product_data=data, number='')
        self.db.add_notification(notification=notif_dict)

    def deactivate_link(self, link_id):
        self.db.deacticate_link(link_id)

    def _format(self, data: dict, response, full_url: str):
        return {
            'link_id': '',
            'shop_id': '',
            'uuid': response.uuid,
            'full_url': full_url,
            'status_code': response.status_code,
            'elapsed': response.elapsed,
            'shop_name': data['shop_name'],
            'item_name': data['item_name'],
            'current_price': data['current_price'],
            'initial_price': data['initial_price'],
            'image_url': data['image_url']
        }

    def _write_exception(self, exc: Exception, full_url: str) -> None:
        exception_data = {
            'type': exc.__cause__,
            'value': exc.__context__,
            'traceback': exc.__traceback__,
            'string': str(exc),
            'ts': datetime.utcnow(),
            'full_url': full_url
        }
        self.db.add_exception(exception_data)

    @staticmethod
    def _random_interval():
        return randint(950, 1300)/100.235876


if __name__ == '__main__':
    runner = PriceController(SinsayParser, RequestHandler, LinksDatabase)
    urls = [
        'https://www.sinsay.com/pl/pl/majtki-5-pack-8022r-mlc',
        'https://www.sinsay.com/pl/pl/bokserki-3-pack-8848i-09m'
    ]
    for url in urls:
        runner.add_new_link(url, 25)
        sleep(10)
    runner.run()
