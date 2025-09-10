"""
Storage manager for UniLinkUp Telegram Bot
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from models.user_session import UserSession
from models.ping import PingRecord

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manages in-memory storage for user sessions and ping history
    """
    
    def __init__(self):
        """Initialize storage manager with empty collections"""
        self._sessions: Dict[int, UserSession] = {}
        self._ping_history: List[PingRecord] = []
        self._max_ping_history = 100  # Configurable limit
        
        logger.info("StorageManager initialized")
    
    def get_user_session(self, user_id: int, username: str = None) -> UserSession:
        """
        Get or create user session
        
        Args:
            user_id: Telegram user ID
            username: Optional username for new sessions
            
        Returns:
            UserSession: Existing or new user session
        """
        if user_id not in self._sessions:
            logger.info(f"Creating new session for user {user_id}")
            self._sessions[user_id] = UserSession(
                user_id=user_id,
                username=username
            )
        else:
            # Update activity for existing session
            self._sessions[user_id].update_activity()
            
            # Update username if provided and different
            if username and self._sessions[user_id].username != username:
                self._sessions[user_id].username = username
                logger.info(f"Updated username for user {user_id} to {username}")
        
        return self._sessions[user_id]
    
    def update_user_session(self, session: UserSession) -> None:
        """
        Update user session in storage
        
        Args:
            session: UserSession to update
        """
        session.update_activity()
        self._sessions[session.user_id] = session
        logger.debug(f"Updated session for user {session.user_id}")
    
    def remove_user_session(self, user_id: int) -> bool:
        """
        Remove user session from storage
        
        Args:
            user_id: User ID to remove
            
        Returns:
            bool: True if session was removed, False if not found
        """
        if user_id in self._sessions:
            del self._sessions[user_id]
            logger.info(f"Removed session for user {user_id}")
            return True
        return False
    
    def get_all_sessions(self) -> Dict[int, UserSession]:
        """
        Get all user sessions
        
        Returns:
            Dict[int, UserSession]: All user sessions by user ID
        """
        return self._sessions.copy()
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove sessions that haven't been active for specified hours
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            int: Number of sessions cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        inactive_users = []
        
        for user_id, session in self._sessions.items():
            if session.last_activity < cutoff_time:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            del self._sessions[user_id]
        
        if inactive_users:
            logger.info(f"Cleaned up {len(inactive_users)} inactive sessions")
        
        return len(inactive_users)
    
    def get_session_count(self) -> int:
        """
        Get total number of active sessions
        
        Returns:
            int: Number of active sessions
        """
        return len(self._sessions)
    
    def save_ping(self, ping: PingRecord) -> None:
        """
        Save a ping record to history
        
        Args:
            ping: PingRecord to save
        """
        self._ping_history.append(ping)
        
        # Maintain history limit
        if len(self._ping_history) > self._max_ping_history:
            # Remove oldest pings
            excess_count = len(self._ping_history) - self._max_ping_history
            self._ping_history = self._ping_history[excess_count:]
            logger.info(f"Trimmed ping history, removed {excess_count} old records")
        
        logger.info(f"Saved ping: {ping.get_short_summary()}")
    
    def get_recent_pings(self, limit: int = 5) -> List[PingRecord]:
        """
        Get recent ping records
        
        Args:
            limit: Maximum number of pings to return
            
        Returns:
            List[PingRecord]: Recent pings, newest first
        """
        # Return most recent pings (reverse chronological order)
        recent_pings = sorted(
            self._ping_history, 
            key=lambda p: p.timestamp, 
            reverse=True
        )
        
        return recent_pings[:limit]
    
    def get_pings_by_organizer(self, organizer_id: int, limit: int = None) -> List[PingRecord]:
        """
        Get pings organized by a specific user
        
        Args:
            organizer_id: User ID of the organizer
            limit: Optional limit on number of results
            
        Returns:
            List[PingRecord]: Pings by the organizer, newest first
        """
        organizer_pings = [
            ping for ping in self._ping_history 
            if ping.organizer_id == organizer_id
        ]
        
        # Sort by timestamp, newest first
        organizer_pings.sort(key=lambda p: p.timestamp, reverse=True)
        
        if limit:
            organizer_pings = organizer_pings[:limit]
        
        return organizer_pings
    
    def get_pings_by_criteria(self, meetup_type: str = None, location: str = None, 
                             limit: int = None) -> List[PingRecord]:
        """
        Get pings matching specific criteria
        
        Args:
            meetup_type: Optional meetup type filter
            location: Optional location filter
            limit: Optional limit on number of results
            
        Returns:
            List[PingRecord]: Matching pings, newest first
        """
        matching_pings = [
            ping for ping in self._ping_history
            if ping.matches_criteria(meetup_type, location)
        ]
        
        # Sort by timestamp, newest first
        matching_pings.sort(key=lambda p: p.timestamp, reverse=True)
        
        if limit:
            matching_pings = matching_pings[:limit]
        
        return matching_pings
    
    def cleanup_old_pings(self, max_age_days: int = 30) -> int:
        """
        Remove ping records older than specified days
        
        Args:
            max_age_days: Maximum age in days before cleanup
            
        Returns:
            int: Number of pings cleaned up
        """
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        original_count = len(self._ping_history)
        self._ping_history = [
            ping for ping in self._ping_history
            if ping.timestamp >= cutoff_time
        ]
        
        cleaned_count = original_count - len(self._ping_history)
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old ping records")
        
        return cleaned_count
    
    def get_ping_history_count(self) -> int:
        """
        Get total number of ping records
        
        Returns:
            int: Number of ping records
        """
        return len(self._ping_history)
    
    def clear_all_data(self) -> None:
        """
        Clear all stored data (for testing purposes)
        """
        self._sessions.clear()
        self._ping_history.clear()
        logger.warning("All storage data cleared")
    
    def clear_ping_history(self) -> int:
        """
        Clear all ping history
        
        Returns:
            int: Number of pings cleared
        """
        count = len(self._ping_history)
        self._ping_history.clear()
        logger.info(f"Cleared {count} ping records")
        return count
    
    def get_storage_stats(self) -> Dict[str, int]:
        """
        Get storage statistics
        
        Returns:
            Dict[str, int]: Storage statistics
        """
        return {
            "active_sessions": len(self._sessions),
            "ping_records": len(self._ping_history),
            "max_ping_history": self._max_ping_history
        }
    
    def __str__(self) -> str:
        """String representation of storage manager"""
        return (
            f"StorageManager(sessions={len(self._sessions)}, "
            f"pings={len(self._ping_history)})"
        )
    
    def persist_to_file(self, filepath: str) -> bool:
        """
        Persist all data to a JSON file
        
        Args:
            filepath: Path to the file to save data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare data for serialization
            data = {
                "sessions": {
                    str(user_id): session.to_dict() 
                    for user_id, session in self._sessions.items()
                },
                "ping_history": [
                    ping.to_dict() for ping in self._ping_history
                ],
                "metadata": {
                    "saved_at": datetime.now().isoformat(),
                    "max_ping_history": self._max_ping_history,
                    "version": "1.0"
                }
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data persisted to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to persist data to {filepath}: {e}")
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        """
        Load data from a JSON file
        
        Args:
            filepath: Path to the file to load data from
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(filepath):
                logger.info(f"No existing data file found at {filepath}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clear existing data
            self._sessions.clear()
            self._ping_history.clear()
            
            # Load sessions
            if "sessions" in data:
                for user_id_str, session_data in data["sessions"].items():
                    try:
                        user_id = int(user_id_str)
                        session = UserSession.from_dict(session_data)
                        self._sessions[user_id] = session
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Failed to load session for user {user_id_str}: {e}")
            
            # Load ping history
            if "ping_history" in data:
                for ping_data in data["ping_history"]:
                    try:
                        ping = PingRecord.from_dict(ping_data)
                        self._ping_history.append(ping)
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Failed to load ping record: {e}")
            
            # Load metadata
            if "metadata" in data:
                metadata = data["metadata"]
                if "max_ping_history" in metadata:
                    self._max_ping_history = metadata["max_ping_history"]
                
                logger.info(f"Loaded data from {filepath} (saved at {metadata.get('saved_at', 'unknown')})")
            
            logger.info(f"Loaded {len(self._sessions)} sessions and {len(self._ping_history)} pings")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load data from {filepath}: {e}")
            return False
    
    def auto_save_enabled(self, filepath: str, interval_minutes: int = 30) -> None:
        """
        Enable automatic periodic saving (placeholder for future implementation)
        
        Args:
            filepath: Path to save file
            interval_minutes: Save interval in minutes
        """
        # This would be implemented with a background task/timer in a full implementation
        logger.info(f"Auto-save configured for {filepath} every {interval_minutes} minutes")
    
    def create_backup(self, filepath: str) -> str:
        """
        Create a backup of the current data file
        
        Args:
            filepath: Original file path
            
        Returns:
            str: Backup file path if successful, empty string otherwise
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"No file to backup at {filepath}")
                return ""
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{filepath}.backup_{timestamp}"
            
            # Copy file content
            with open(filepath, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            logger.info(f"Backup created at {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return ""
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging"""
        return (
            f"StorageManager(sessions={len(self._sessions)}, "
            f"pings={len(self._ping_history)}, "
            f"max_history={self._max_ping_history})"
        )