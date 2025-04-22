import mysql.connector
from mysql.connector.pooling import PooledMySQLConnection
from loguru import logger

from api.services.music.spotify_data_service import TimeRange


class DBServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class DBService:
    def __init__(self, connection: PooledMySQLConnection):
        self.connection = connection

    def create_user(self, user_id: str, refresh_token: str):
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO spotify_user (id, refresh_token) VALUES (%s, %s);",
                (user_id, refresh_token)
            )
            cursor.close()
            self.connection.commit()
        except mysql.connector.Error as e:
            self.connection.rollback()
            error_message = f"Failed to create user. User ID: {user_id}, refresh token: {refresh_token}"
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)

    def get_latest_dates(self, user_id: str, limit: int = 2) -> list[str]:
        try:
            cursor = self.connection.cursor(dictionary=True)
            select_statement = f"""
                SELECT collected_date as day
                FROM top_artist
                WHERE spotify_user_id = %s
                GROUP BY day
                ORDER BY day DESC
                LIMIT {limit};
            """
            cursor.execute(select_statement, (user_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except mysql.connector.Error as e:
            error_message = f"Failed to get latest dates. User ID: {user_id}"
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)

    def get_top_artists(self, user_id: str, time_range: TimeRange) -> list[dict]:
        try:
            cursor = self.connection.cursor(dictionary=True)
            select_statement = (
                "WITH most_recent_date AS ("
                    "SELECT collected_date "
                    "FROM top_artist "
                    "WHERE spotify_user_id = %s "
                    "AND time_range = %s "
                    "ORDER BY collected_date DESC "
                    "LIMIT 1"
                ")"
                "SELECT * " 
                "FROM top_artist ta "
                "JOIN most_recent_date rd " 
                "ON ta.collected_date = rd.collected_date "
                "WHERE ta.spotify_user_id = %s "
                "AND ta.time_range = %s "
                "ORDER BY ta.position;"
            )
            cursor.execute(select_statement, (user_id, time_range.value, user_id, time_range.value))
            results = cursor.fetchall()
            cursor.close()
            return results
        except mysql.connector.Error as e:
            error_message = f"Failed to get top artists. User ID: {user_id}, time range: {time_range.value}"
            logger.error(f"{error_message} - {e}")
            raise DBServiceException(error_message)
