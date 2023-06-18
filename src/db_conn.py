import sqlite3
from datetime import datetime


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
			created_ts TEXT DETAULT CURRENT_TIMESTAMP,
            CONSTRAINT unieque_links_full_url UNIQUE(full_url) ON CONFLICT REPLACE,
            CONSTRAINT unieque_links_link_id_shop_id UNIQUE(link_id, shop_id) ON CONFLICT REPLACE,
            CONSTRAINT fk_links_shop_id FOREIGN KEY (shop_id) REFERENCES shops (shop_id) ON DELETE CASCADE
            );
        
        CREATE TABLE IF NOT EXISTS prices (
            price_id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INT NOT NULL,
            current_price NUMERIC(4, 2) NOT NULL,
            ts TEXT DETAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_prices_link_id FOREIGN KEY (link_id) REFERENCES links (link_id) ON DELETE CASCADE
            );
        
        CREATE TABLE IF NOT EXISTS shops (
            shop_id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name VARCHAR(200),
            created_ts TEXT DETAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_shop_shop_name UNIQUE(shop_name) ON CONFLICT IGNORE
        );
        """

        cur = self.conn.cursor()
        cur.executescript(tables_ddl)
        cur.connection.commit()
        cur.close()
