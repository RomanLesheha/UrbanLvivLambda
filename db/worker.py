import pymysql
import json


class DBWorker:
    def __init__(self, host, user, password, database, init_db=False):
        self.db_connection = None  # Initialize db_connection to None
        if init_db:
            self.connect_to_db(host, user, password, database)

    def connect_to_db(self, host, user, password, database):
        """Establish a database connection."""
        self.db_connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

    def run_query(self, query, params=None):
        if not self.db_connection:  # Check if the connection exists
            raise AttributeError("Database connection is not initialized. Call `connect_to_db` first.")

        with self.db_connection.cursor() as cursor:
            cursor.execute(query, params)
            self.db_connection.commit()
            return cursor

    def fetch_all_as_dict(self, cursor):
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


    def call_get_report_details(self, report_id):
        sql = "CALL get_report_details_for_ai_process(%s)"
        params = (report_id,)

        cursor = self.run_query(sql, params)
        results = self.fetch_all_as_dict(cursor)

        if results:
            return results[0]

        return results

    def create_report_details_with_ai_answer(self, report_id, recommendations, short_answer, official_summary, suggest_priority_id):
        sql = "CALL create_report_details_with_ai_answer(%s, %s, %s, %s, %s)"
        params = (
            report_id,
            recommendations,
            short_answer,
            official_summary,
            suggest_priority_id
        )
        self.run_query(sql, params)

