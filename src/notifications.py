import requests

from datetime import datetime

from secret import SMS_APIKEY, SMS_PASSWORD, SMS_NAME


class Notification:

    sms_url = 'https://api2.smsplanet.pl/sms'

    @classmethod
    def send_text(cls, product_data: dict, number: str) -> dict:
        print(f'[SMS]\t[{datetime.utcnow()}]\t Preparing message to be sent')
        cls.validate_number(number)
        message = cls.build_message(product_data, message_type='text')
        data = {
            'key': SMS_APIKEY,
            'password': SMS_PASSWORD,
            'from': SMS_NAME,
            'to': number,
            'msg': message
        }
        response = requests.post(url=cls.sms_url, data=data, timeout=10)

        try:
            response.raise_for_status()
            message_id = response.json()['messageId']
            print(f'[SMS]\t[{datetime.utcnow()}]\t MESSAGE SENT')
            return cls.get_status(id=message_id)
        except requests.exceptions.HTTPError:
            print(f'[SMS]\t[{datetime.utcnow()}]\t FAILED')
            return cls.get_status(status='FAILED_HTTP')
        except KeyError:
            fail_id = ', '.join(response.json())
            print(f'[SMS]\t[{datetime.utcnow()}]\t FAILED')
            return cls.get_status(id=fail_id, status='FAILED_TEXT')

    @classmethod
    def send_email(cls, message: str, email_address: str) -> bool:
        pass

    @staticmethod
    def build_message(data: dict, message_type: str) -> str:
        if message_type == 'text':
            return f"""Spadek ceny z {data['old_price']} na {data['new_price']} {data['full_url']}"""

    @classmethod
    def get_status(cls, id: str='', status: str='OK'):
        return {
            'status': status,
            'id': id,
            'ts': datetime.utcnow()
        }

    @staticmethod
    def validate_number(number: str):
        if len(number) < 9:
            raise ValueError(f'Provided number "{number}" is too short')
        if len(number) > 9:
            raise ValueError(f'Provided number "{number}" is too long')
        if not number.isdigit():
            raise ValueError(f'"{number}" is not a valid phone number.')