from src.send_request import RequestHandler
from headers.cookie_policies import BlockAll
from src.parsers import SinsayParser, BaseParser
from src.db_conn import LinksDatabase



class PriceController:

    def __init__(self, parser: BaseParser, request_handler: RequestHandler, db: LinksDatabase):
        self.parser: BaseParser = parser
        self.request_handler: RequestHandler = request_handler
        self.db: LinksDatabase = db()

    def run(self):
        # A forever working loop
        # Sleep and check each 15 minutes for links to be updated
        pass

    def get_links_to_check(self):
        # Fetch links which had their price checked over 4h ago
        # Check is is_active is 'y' (no need to pointlessly hit a 404)
        pass
    
    def notify_change_in_price(self):
        # Nofify by SMS that a price has changed
        # And forefuly notify if below price treshold :D
        pass
    
    def check(self, full_url: str, headers: dict):
        request_handler = self.request_handler(headers)
        response = request_handler.send_request(full_url, cookie_policy=BlockAll)
        data = self.parser(response.content).get()
        complete_data = self._format(data, response, full_url)

        link_id = self.db.get_link_id_by_url(full_url)
        if not link_id:
            link_id = self.db.add_link(complete_data)
        
        self.db.add_price(complete_data, link_id)

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


from headers.sinsay import HEADERS as sinsay_headers
from time import sleep
from random import randint
urls = [
    'https://www.sinsay.com/pl/pl/sukienka-maxi-ze-wzorem-2-6582t-03x',
    'https://www.sinsay.com/pl/pl/sukienka-mini-dzianinowa-5912j-40x',
    'https://www.sinsay.com/pl/pl/sukienka-mini-na-ramiaczkach-9044t-33x',

]

controller = PriceController(SinsayParser, RequestHandler, LinksDatabase)
for url in urls:
    controller.check(url, sinsay_headers)
    sleep(randint(400, 800)/100.235876)
