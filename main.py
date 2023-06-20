from src.send_request import RequestHandler
from headers.cookie_policies import BlockAll
from src.parsers import SinsayParser, BaseParser
from src.db_conn import LinksDatabase
from headers.default import DEFAULT_HEADERS


import asyncio, aiohttp
from datetime import datetime
from time import sleep
from random import randint



class PriceController:

    default_headers = DEFAULT_HEADERS

    def __init__(self, parser: BaseParser, request_handler: RequestHandler, db: LinksDatabase):
        self.parser: BaseParser = parser
        self.request_handler: RequestHandler = request_handler
        self.db: LinksDatabase = db()

    def run(self):
        links_todo = self.get_links_to_check()
        if links_todo:
            for shop_id, (url_list, link_id) in links_todo.items():
                headers = self.db.get_headers(shop_id)
                for full_url in url_list:
                    try:
                        complete_data = self.get_product_data(full_url, headers)
                        self.db.add_price(complete_data, link_id)
                    except Exception as exc:
                        exception_data = {
                            'type': exc.__cause__,
                            'value': exc.__context__,
                            'traceback': exc.__traceback__,
                            'string': str(exc),
                            'ts': datetime.now(),
                            'full_url': full_url
                        }
                        print(f'[RUN] Hurt myself while processing {full_url}')
                        self.db.add_exception(exception_data)
                    finally:
                        sleep(self.random_interval())
            print('[RUN] Finished. Sleepy time.')
        else:
            print('[RUN] Nothing to do. Sleep.')

        sleep(900)

    def add_new_link(self, full_url: str, price_alert_treshold: int=None):
        complete_data = self.get_product_data(full_url, self.default_headers)
        complete_data['price_alert_treshold'] = (
            price_alert_treshold
            if price_alert_treshold
            else int(float(complete_data['current_price']) * 0.5)
        )
        self.db.add_link(complete_data)

    def get_links_to_check(self) -> dict[str]:
        print('[LOG] Getting links to check.')
        links_by_shops = {}
        for link_id ,shop_id, full_url in self.db.get_links_for_cycle():
            if not links_by_shops.get(shop_id, []):
                links_by_shops[shop_id] = ([full_url], link_id)
            else:
                links_by_shops[shop_id][0].append(full_url)
        print(f'[LOG] Got {len(links_by_shops)}')
        return links_by_shops
    
    def notify_change_in_price(self):
        # Nofify by SMS that a price has changed
        # And forefuly notify if below price treshold :D
        pass
    
    def get_product_data(self, full_url: str, headers: dict) -> dict[str]:
        print(f'[LOG] Getting {full_url}')
        request_handler = self.request_handler(headers)
        response = request_handler.send_request(full_url, cookie_policy=BlockAll)
        data = self.parser(response.content).get()
        print(f'[LOG] OK')
        return self._format(data, response, full_url)

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

    @staticmethod
    def random_interval():
        return randint(950, 1300)/100.235876



# urls = [
#     'https://www.sinsay.com/pl/pl/sukienka-maxi-ze-wzorem-2-6582t-03x',
#     'https://www.sinsay.com/pl/pl/sukienka-mini-dzianinowa-5912j-40x',
#     'https://www.sinsay.com/pl/pl/sukienka-mini-na-ramiaczkach-9044t-33x'
# ]

# controller = PriceController(SinsayParser, RequestHandler, LinksDatabase)
# for url in urls:
#     controller.get_product_data(url, DEFAULT_HEADERS)
#     sleep(randint(400, 800)/100.235876)

if __name__ == '__main__':
    runner = PriceController(SinsayParser, RequestHandler, LinksDatabase)
    while True:
        try:
            runner.run()
        except Exception:
            pass
