# Add these methods to PublishingSystem class:


    def get_share_access_history(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Get the access history for a folder showing all published versions.
        
        This helps track which users have access to which versions,
        remembering that ALL historical versions remain accessible forever.
        """
        shares = self.db.get_folder_shares(folder_id)
        history = []
        
        for share in shares:
            # Get authorized users for this version
            auth_users = None
            if share['share_type'] == 'private':
                # Extract from index if stored
                auth_users = self._get_share_authorized_users(share['share_id'])
                
            history.append({
                'share_id': share['share_id'],
                'version': share['version'],
                'published_at': share['created_at'],
                'share_type': share['share_type'],
                'access_string': share['access_string'],
                'is_active': share.get('is_active', True),
                'authorized_users': auth_users,
                'permanent_on_usenet': True,  # Always true!
                'note': 'This share is permanently accessible to authorized users'
            })
            
        return history

    def _get_share_authorized_users(self, share_id: str) -> Optional[List[str]]:
        """Get authorized users for a specific share"""
        # This would need to retrieve from stored index metadata
        # For now, return None as this info might not be stored
        return None
