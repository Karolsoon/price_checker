import sqlite3
from datetime import datetime
import json


DATABASE_PATH = 'data/links.db'

class LinksDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(
            DATABASE_PATH,
            timeout=2.0
            )
        self.cur = None
        self.__create_tables()

    def __enter__(self):
        self.cur = self.conn.cursor()
        return self.cur

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.cur = None

        if isinstance(exc_value, IndexError):
            # Some handling here
            return True # Indicates swallowing the exception

        return None
        # Returning false here causes no harm since no exception was raised?

    def get_links_for_cycle(self) -> list[tuple]:
        query = """
            WITH most_recent_prices AS (
                    SELECT
                        link_id,
                        price_id,
                        ts,
                        ROW_NUMBER() OVER(PARTITION BY link_id ORDER BY ts DESC) AS recent
                    FROM prices)
                

                SELECT l.link_id, s.shop_id, l.full_url
                FROM links l
                INNER JOIN most_recent_prices p ON p.link_id = l.link_id
                INNER JOIN shops s ON s.shop_id = l.shop_id
                WHERE l.is_active = 'y'
                AND p.recent = 1
                AND (julianday(CURRENT_TIMESTAMP) - julianday(p.ts)) * 3600 > 240
        """
        cur = self.conn.cursor()
        links = cur.execute(query).fetchall()
        cur.close()
        return links

    def add_link(self, complete_data: dict):
        shop_id = self.get_shop_id_by_name(complete_data['shop_name'])
        if not shop_id:
            shop_id = self.add_shop(complete_data['shop_name'])

        new_link_query = f"""
        INSERT INTO links (shop_id, full_url, item_name, price_alert_treshold, created_ts) VALUES 
        ( {shop_id}, '{complete_data['full_url']}', '{complete_data['item_name']}', {25}, '{datetime.now()}');
        """
        self.execute_sql(new_link_query)

        cur = self.conn.cursor()
        cur.execute(f"""SELECT link_id FROM links WHERE full_url = '{complete_data['full_url']}'""")
        link_id = cur.fetchone()
        cur.close()
        return link_id[0]


    def add_price(self, complete_data: dict, link_id: int):
        print(f"""[DB] Adding {complete_data['current_price']} for {complete_data['item_name']}""")
        price_query = f"""
        INSERT INTO prices (link_id, current_price, ts) VALUES
        ({link_id}, {complete_data['current_price']}, '{datetime.now()}');
        """
        self.execute_sql(price_query)
        return True

    def add_shop(self, shop_name: str) -> int:
        query = f"""
        INSERT INTO shops (shop_name, created_ts) VALUES
        ('{shop_name}', '{datetime.now()}');
        """
        self.execute_sql(query)
        print('[INSERT] Shop added!')

        shop_id_query = f"""
        SELECT shop_id
        FROM shops
        WHERE UPPER(shop_name) = UPPER('{shop_name}')
        """
        cur = self.conn.cursor()
        shop_id = cur.execute(shop_id_query).fetchone()
        cur.close()
        return shop_id[0]
    
    def add_exception(self, exc: dict) -> None:
        query = f"""
        INSERT INTO exceptions (exception_type, exception_value, exception_traceback, exception_string, ts, full_url) VALUES
        ('{exc['type']}', '{exc['value']}', '{exc['traceback']}', '{exc['string']}', '{exc['ts']}', '{exc['full_url']}')
        """
        self.execute_sql(query)

    def update_link(self, complete_data: dict, id_dict: str) -> None:
        update_query = f"""
        UPDATE links
            SET shop_id = '{id_dict['shop_id']}',
                item_name = '{complete_data['item_name']}'
            WHERE link_id = '{id_dict['link_id']}';
        """
        self.execute_sql(update_query)
        print('[UPDATE] Success!')

        shop_id = self.add_shop(complete_data['shop_name'])
        new_link_query = f"""
        INSERT INTO links (shop_id, full_url, item_name, price_alert_treshold, created_ts) VALUES 
        ( {shop_id}, '{complete_data['full_url']}', '{complete_data['item_name']}', {25}, '{datetime.now()}');
        """
        self.execute_sql(new_link_query)

    def deacticate_link(self, link_id: str) -> None:
        deactivate_query = f"""
        UPDATE links
            SET is_active = 'n'
            WHERE link_id = '{link_id}';
        """
        self.execute_sql(deactivate_query)

    def get_link_id_by_url(self, url: str):
        cur = self.conn.cursor()
        cur.execute(f"SELECT link_id FROM links WHERE full_url = '{url}'")
        link_id = cur.fetchone()
        cur.close()
        return link_id[0] if isinstance(link_id, tuple) else link_id

    def get_shop_id_by_name(self, shop_name: str):
        cur = self.conn.cursor()
        cur.execute(f"SELECT shop_id FROM shops WHERE lower(shop_name) = lower('{shop_name}')")
        shop_id = cur.fetchone()
        cur.close()
        return shop_id[0] if isinstance(shop_id, tuple) else shop_id

    def get_headers(self, shop_id) -> dict:
        query = f"""
        SELECT headers
        FROM shops
        WHERE shop_id = {shop_id}
        """
        cur = self.conn.cursor()
        headers = cur.execute(query).fetchone()
        cur.close()
        return json.loads(headers[0])

    def execute_sql(self, query: str) -> None:
        # print('[EXECUTE_SQL]: ', query)
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()
        cur.close()

    def __create_tables(self):
        tables_ddl = """
        CREATE TABLE IF NOT EXISTS links (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INT NULL DEFAULT -1,
            full_url VARCHAR(500) NOT NULL,
            item_name VARCHAR(200) NULL,
            visiting_interval_in_hours INT NOT NULL DEFAULT 4,
            price_alert_treshold NUMERIC(4,2) NULL,
            is_active NCHAR(1) NOT NULL DEFAULT 'y',
			created_ts TEXT DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unieque_links_full_url UNIQUE(full_url) ON CONFLICT REPLACE,
            CONSTRAINT unieque_links_link_id_shop_id UNIQUE(link_id, shop_id) ON CONFLICT REPLACE,
            CONSTRAINT fk_links_shop_id FOREIGN KEY (shop_id) REFERENCES shops (shop_id) ON DELETE CASCADE
            );
        
        CREATE TABLE IF NOT EXISTS prices (
            price_id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INT NOT NULL,
            current_price NUMERIC(4, 2) NOT NULL,
            ts TEXT DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_prices_link_id FOREIGN KEY (link_id) REFERENCES links (link_id) ON DELETE CASCADE
            );
        
        CREATE TABLE IF NOT EXISTS shops (
            shop_id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name VARCHAR(200) NULL,
            headers VARCHAR(4000) NULL,
            created_ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_shop_shop_name UNIQUE(shop_name) ON CONFLICT IGNORE
            );
        
        CREATE TABLE IF NOT EXISTS exceptions (
            exception_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exception_type VARCHAR(100) NOT NULL,
            exception_value VARCHAR(200) NOT NULL,
            exception_traceback TEXT NOT NULL,
            exception_string VARCHAR(400),
            full_url VARCHAR(200) NOT NULL,
            ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """

        cur = self.conn.cursor()
        cur.executescript(tables_ddl)
        cur.connection.commit()
        cur.close()
