from bs4 import BeautifulSoup


import re
import json


class BaseParser:

    js_keyword: str = ...
    regex: re = ...

    def get(self) -> dict[str]:
        pass

    def set_item(self, raw: dict) -> None:
        pass

    def find_data_tag(self) -> str:
        pass

    def get_name_from_title_tag(self) -> str:
        pass

    def transform_data_tag(self, js_text: str) -> dict[str]:
        pass


class SinsayParser(BaseParser):

    js_keyword = 'dataLayer.push('
    regex = re.compile(r'' +re.escape(js_keyword) + r'(.*?)}')

    def __init__(self, content: bytes):
        self.soup = BeautifulSoup(content, 'html.parser')
        self.shop_name = ''
        self.item_name = ''
        self.current_price = ''
        self.initial_price = ''
        self.image_url = ''


    def get(self) -> dict[str]:
        js_text = self.find_data_tag()
        raw_data = self.transform_data_tag(js_text)
        self.set_item(raw_data)

        self.shop_name = self.get_name_from_title_tag()
        return {
            'shop_name': self.shop_name,
            'item_name': self.item_name,
            'current_price': self.current_price,
            'initial_price': self.initial_price,
            'image_url': self.image_url
        }

    def set_item(self, raw: dict) -> None:
        self.item_name = raw['name']
        self.current_price = raw['price'].replace(',', '.')
        self.initial_price = raw['basePrice'].replace(',', '.')
        self.image_url = raw['imageUrl']

    def find_data_tag(self) -> str:
        body = self.soup.find('body')
        js_tags = body.find_all('script')
        js_tags_l = [x.text for x in js_tags]

        filtered_js_tags = [x for x in js_tags_l if self.js_keyword in x]

        return filtered_js_tags[0]

    def get_name_from_title_tag(self) -> str:
        title = self.soup.find('title')
        title_elements = title.text.split(',')
        return title_elements[1].strip()

    def transform_data_tag(self, js_text: str) -> dict[str]:
        api_data_json = self.regex.search(js_text).group()
        api_data_json = api_data_json.replace(self.js_keyword, '')
        return json.loads(api_data_json)


class HMParser(BaseParser):

    js_keyword = 'utag_data = '
    regex = re.compile(r'' +re.escape(js_keyword) + r'(.*?) event_type')

    def __init__(self, content: bytes):
        self.soup = BeautifulSoup(content, 'html.parser')
        self.shop_name = ''
        self.item_name = ''
        self.current_price = ''
        self.initial_price = ''
        self.image_url = ''


    def get(self) -> dict[str]:
        js_text = self.find_data_tag()
        raw_data = self.transform_data_tag(js_text)
        self.set_item(raw_data)

        self.shop_name = self.get_name_from_title_tag()
        return {
            'shop_name': self.shop_name,
            'item_name': self.item_name,
            'current_price': self.current_price,
            'initial_price': self.initial_price,
            'image_url': self.image_url
        }

    def set_item(self, raw: dict) -> None:
        self.item_name = raw['product_name']
        self.current_price = raw['product_list_price'].replace(',', '.')
        self.initial_price = raw['product_original_price'].replace(',', '.')
        self.image_url = 'Requires additional extraction'

    def find_data_tag(self) -> str:
        tag = self.soup.find('div', {'class': 'tealiumProductviewtag productview parbase'}, True)
        return tag.select_one('script').decode_contents()

    def get_name_from_title_tag(self) -> str:
        title = self.soup.find('title')
        title_elements = title.text.strip().split('|') #product name | H&amp;M PL
        return title_elements[1].strip().split(' ')[0].replace(r'&amp;', '&')

    def transform_data_tag(self, js_text: str) -> dict[str]:
        api_data_dict = {}
        api_data_str = self.regex.search(js_text).group()
        items_str = api_data_str.replace(self.js_keyword, '').replace('["', '').replace('"]', '')[1:-12].split(',')
        for item in items_str:
            key, value = item.split(':')
            api_data_dict[key.strip()] = value.strip()
        return api_data_dict
