import psycopg2


class DBService:
    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn

    def create_user(self, user_id: str, refresh_token: str):
        with self.conn.cursor() as cur:
            insert_statement = """
                INSERT INTO spotify_user(id, refresh_token)
                VALUES(?, ?);
            """
            cur.execute(insert_statement, (user_id, refresh_token))
