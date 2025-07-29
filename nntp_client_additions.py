# Add this method to ProductionNNTPClient class:


    def retrieve_article(self, message_id: str, newsgroup: str) -> Optional[bytes]:
        """Retrieve article from Usenet"""
        try:
            with self.connection_pool.get_connection() as conn:
                return conn.retrieve_article(message_id, newsgroup)
        except Exception as e:
            logger.error(f"Error retrieving article: {e}")
            return None
