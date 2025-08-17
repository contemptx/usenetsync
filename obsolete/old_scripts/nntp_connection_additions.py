# Add this method to NNTPConnection class:


    def retrieve_article(self, message_id: str, newsgroup: str) -> Optional[bytes]:
        """Retrieve article by message ID"""
        with self._lock:
            if not self.connection:
                raise Exception("Connection not established")
            
            try:
                # pynntp uses a different API than nntplib
                # First, ensure we're in the right group
                self.connection.group(newsgroup)
                
                # Retrieve article by message ID
                # pynntp's article method returns (response, article_num, message_id, text)
                response = self.connection.article(message_id)
                
                if response and len(response) >= 4:
                    # response[3] contains the article lines
                    article_lines = response[3]
                    
                    # Join lines - they come as a list of bytes
                    article_data = b'\r\n'.join(article_lines)
                    
                    # Find body start (after headers)
                    header_end = article_data.find(b'\r\n\r\n')
                    if header_end != -1:
                        headers = article_data[:header_end]
                        body_data = article_data[header_end + 4:]
                        
                        # Check if base64 encoded
                        if b'Content-Transfer-Encoding: base64' in headers:
                            import base64
                            try:
                                body_data = base64.b64decode(body_data)
                            except:
                                pass  # Not valid base64, use as-is
                                
                        return body_data
                    else:
                        # No clear header boundary, return all
                        return article_data
                        
                return None
                        
            except Exception as e:
                logger.error(f"Failed to retrieve article {message_id}: {e}")
                return None
