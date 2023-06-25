TODO:
1. Add image_url to links table
2. Add table or column for the phone number where the text message should be sent
3. API for adding links interactively while the price checker sleeps - preferrably async or concurrent.
4. Add more sites to the parser.
5. Refactor (clean code) the run method - extract out the try-except block


Exceptions
sqlite3.OperationalError: database is locked
sqlite3.OperationalError: no such column: s.link_id