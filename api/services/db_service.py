import mysql.connector
from mysql.connector.pooling import PooledMySQLConnection


class DBService:
    def __init__(self, conn: PooledMySQLConnection):
        self.conn = conn

    def create_user(self, user_id: str, refresh_token: str):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO spotify_user (id, refresh_token) VALUES (%s, %s);",
                    (user_id, refresh_token)
                )
                self.conn.commit()
        except mysql.connector.IntegrityError:
            self.conn.rollback()
