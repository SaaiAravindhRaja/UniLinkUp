"""
Recent pings handler for UniLinkUp Telegram Bot
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from handlers.base import BaseHandler
from ui.messages import MessageFormatter
from config.constants import MAX_RECENT_PINGS

logger = logging.getLogger(__name__)


class RecentHandler(BaseHandler):
    """
    Handler for displaying recent ping invitations
    """
    
    async def recent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /recent command - show recent ping invitations
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            user_id = self._get_user_id(update)
            username = self._get_username(update)
            
            if not user_id:
                await self.handle_error(update, context, 
                                      Exception("No user ID found"), 
                                      "Unable to identify user")
                return
            
            # Log the command
            self._log_user_action(user_id, "recent_command", f"username: {username}")
            
            # Send typing action
            await self._send_typing_action(update, context)
            
            # Get recent pings from storage
            recent_pings = self.storage.get_recent_pings(limit=MAX_RECENT_PINGS)
            
            # Format the message
            message = MessageFormatter.format_recent_pings(recent_pings)
            
            # Send the message
            success = await self._safe_reply(update, message)
            
            if success:
                self.logger.info(f"Recent pings displayed for user {user_id} ({len(recent_pings)} pings)")
            else:
                self.logger.warning(f"Failed to send recent pings for user {user_id}")
                
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to retrieve recent invitations")
    
    async def get_user_recent_pings(self, user_id: int, limit: int = None) -> list:
        """
        Get recent pings organized by a specific user
        
        Args:
            user_id: User ID to get pings for
            limit: Optional limit on number of results
            
        Returns:
            list: List of PingRecord objects organized by the user
        """
        try:
            if limit is None:
                limit = MAX_RECENT_PINGS
            
            user_pings = self.storage.get_pings_by_organizer(user_id, limit=limit)
            
            self.logger.info(f"Retrieved {len(user_pings)} pings for user {user_id}")
            return user_pings
            
        except Exception as e:
            self.logger.error(f"Failed to get user pings for {user_id}: {e}")
            return []
    
    async def get_recent_pings_by_type(self, meetup_type: str, limit: int = None) -> list:
        """
        Get recent pings filtered by meetup type
        
        Args:
            meetup_type: Type of meetup ("lunch" or "study")
            limit: Optional limit on number of results
            
        Returns:
            list: List of PingRecord objects of the specified type
        """
        try:
            if limit is None:
                limit = MAX_RECENT_PINGS
            
            type_pings = self.storage.get_pings_by_criteria(
                meetup_type=meetup_type, 
                limit=limit
            )
            
            self.logger.info(f"Retrieved {len(type_pings)} {meetup_type} pings")
            return type_pings
            
        except Exception as e:
            self.logger.error(f"Failed to get {meetup_type} pings: {e}")
            return []
    
    async def get_recent_pings_by_location(self, location: str, limit: int = None) -> list:
        """
        Get recent pings filtered by location
        
        Args:
            location: Location to filter by
            limit: Optional limit on number of results
            
        Returns:
            list: List of PingRecord objects at the specified location
        """
        try:
            if limit is None:
                limit = MAX_RECENT_PINGS
            
            location_pings = self.storage.get_pings_by_criteria(
                location=location, 
                limit=limit
            )
            
            self.logger.info(f"Retrieved {len(location_pings)} pings at {location}")
            return location_pings
            
        except Exception as e:
            self.logger.error(f"Failed to get pings for location {location}: {e}")
            return []
    
    def get_ping_statistics(self) -> dict:
        """
        Get statistics about ping history
        
        Returns:
            dict: Statistics about pings
        """
        try:
            all_pings = self.storage.get_recent_pings(limit=1000)  # Get more for stats
            
            if not all_pings:
                return {
                    "total_pings": 0,
                    "lunch_pings": 0,
                    "study_pings": 0,
                    "unique_organizers": 0,
                    "unique_locations": set(),
                    "most_popular_location": None
                }
            
            lunch_count = sum(1 for ping in all_pings if ping.meetup_type == "lunch")
            study_count = sum(1 for ping in all_pings if ping.meetup_type == "study")
            
            organizers = set(ping.organizer_id for ping in all_pings)
            locations = [ping.location for ping in all_pings]
            unique_locations = set(locations)
            
            # Find most popular location
            location_counts = {}
            for location in locations:
                location_counts[location] = location_counts.get(location, 0) + 1
            
            most_popular_location = max(location_counts.items(), key=lambda x: x[1])[0] if location_counts else None
            
            return {
                "total_pings": len(all_pings),
                "lunch_pings": lunch_count,
                "study_pings": study_count,
                "unique_organizers": len(organizers),
                "unique_locations": unique_locations,
                "most_popular_location": most_popular_location
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get ping statistics: {e}")
            return {"error": str(e)}
    
    async def send_ping_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Send ping statistics to user (for debugging/admin use)
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            user_id = self._get_user_id(update)
            
            if user_id:
                self._log_user_action(user_id, "ping_statistics_requested")
            
            stats = self.get_ping_statistics()
            
            if "error" in stats:
                await self._safe_reply(update, f"⚠️ Error getting statistics: {stats['error']}")
                return
            
            stats_message = f"""
📊 **UniLinkUp Statistics**

📋 Total invitations: {stats['total_pings']}
🍽️ Lunch meetups: {stats['lunch_pings']}
📚 Study sessions: {stats['study_pings']}
👥 Active organizers: {stats['unique_organizers']}
📍 Unique locations: {len(stats['unique_locations'])}
🏆 Most popular location: {stats['most_popular_location'] or 'None'}
            """.strip()
            
            await self._safe_reply(update, stats_message)
            
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to get statistics")
    
    async def cleanup_old_pings(self, max_age_days: int = 30) -> int:
        """
        Clean up old ping records
        
        Args:
            max_age_days: Maximum age in days before cleanup
            
        Returns:
            int: Number of pings cleaned up
        """
        try:
            cleaned_count = self.storage.cleanup_old_pings(max_age_days)
            
            self.logger.info(f"Cleaned up {cleaned_count} old ping records (older than {max_age_days} days)")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old pings: {e}")
            return 0


# Standalone command function for use with CommandHandler
async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Standalone recent command function
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        await update.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return
    
    handler = RecentHandler(storage_manager)
    await handler.recent_command(update, context)


async def ping_statistics_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Standalone ping statistics command function (for debugging)
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        await update.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return
    
    handler = RecentHandler(storage_manager)
    await handler.send_ping_statistics(update, context)