"""
Unit tests for KeyboardFactory
"""

import unittest
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ui.keyboards import KeyboardFactory
from models.user_session import UserSession
from config.constants import LOCATIONS, FRIENDS, CALLBACK_LOCATION, CALLBACK_FRIEND, CALLBACK_CONFIRM


class TestKeyboardFactory(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 12345
        self.session = UserSession(user_id=self.user_id, username="testuser")
    
    def test_create_location_keyboard(self):
        """Test location keyboard creation"""
        keyboard = KeyboardFactory.create_location_keyboard()
        
        self.assertIsInstance(keyboard, InlineKeyboardMarkup)
        
        # Check that all locations are included
        all_buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                all_buttons.append(button)
        
        self.assertEqual(len(all_buttons), len(LOCATIONS))
        
        # Check button texts and callback data
        for i, button in enumerate(all_buttons):
            self.assertEqual(button.text, LOCATIONS[i])
            self.assertEqual(button.callback_data, f"{CALLBACK_LOCATION}{i}")
    
    def test_create_friends_keyboard_no_selection(self):
        """Test friends keyboard with no friends selected"""
        keyboard = KeyboardFactory.create_friends_keyboard(self.session)
        
        self.assertIsInstance(keyboard, InlineKeyboardMarkup)
        
        # Count friend buttons (excluding action buttons in last row)
        friend_buttons = []
        for row in keyboard.inline_keyboard[:-1]:  # Exclude last row (action buttons)
            for button in row:
                friend_buttons.append(button)
        
        self.assertEqual(len(friend_buttons), len(FRIENDS))
        
        # All friends should show as unselected (⬜)
        for button in friend_buttons:
            self.assertTrue(button.text.startswith("⬜"))
        
        # Check action buttons - should only have Cancel (no Confirm without selections)
        action_row = keyboard.inline_keyboard[-1]
        self.assertEqual(len(action_row), 1)
        self.assertIn("Cancel", action_row[0].text)
    
    def test_create_friends_keyboard_with_selection(self):
        """Test friends keyboard with some friends selected"""
        # Select some friends
        self.session.toggle_friend("Alex")
        self.session.toggle_friend("Sam")
        
        keyboard = KeyboardFactory.create_friends_keyboard(self.session)
        
        # Find Alex and Sam buttons
        alex_button = None
        sam_button = None
        jordan_button = None
        
        for row in keyboard.inline_keyboard[:-1]:
            for button in row:
                if "Alex" in button.text:
                    alex_button = button
                elif "Sam" in button.text:
                    sam_button = button
                elif "Jordan" in button.text:
                    jordan_button = button
        
        # Selected friends should show ✅
        self.assertIsNotNone(alex_button)
        self.assertTrue(alex_button.text.startswith("✅"))
        
        self.assertIsNotNone(sam_button)
        self.assertTrue(sam_button.text.startswith("✅"))
        
        # Unselected friends should show ⬜
        self.assertIsNotNone(jordan_button)
        self.assertTrue(jordan_button.text.startswith("⬜"))
        
        # Should have both Confirm and Cancel buttons
        action_row = keyboard.inline_keyboard[-1]
        self.assertEqual(len(action_row), 2)
        
        confirm_button = next(btn for btn in action_row if "Confirm" in btn.text)
        cancel_button = next(btn for btn in action_row if "Cancel" in btn.text)
        
        self.assertIsNotNone(confirm_button)
        self.assertIsNotNone(cancel_button)
    
    def test_create_confirmation_keyboard(self):
        """Test confirmation keyboard creation"""
        keyboard = KeyboardFactory.create_confirmation_keyboard()
        
        self.assertIsInstance(keyboard, InlineKeyboardMarkup)
        self.assertEqual(len(keyboard.inline_keyboard), 1)
        self.assertEqual(len(keyboard.inline_keyboard[0]), 2)
        
        buttons = keyboard.inline_keyboard[0]
        send_button = buttons[0]
        cancel_button = buttons[1]
        
        self.assertIn("Send Invitations", send_button.text)
        self.assertEqual(send_button.callback_data, f"{CALLBACK_CONFIRM}send")
        
        self.assertIn("Cancel", cancel_button.text)
        self.assertEqual(cancel_button.callback_data, f"{CALLBACK_CONFIRM}cancel")
    
    def test_create_time_skip_keyboard(self):
        """Test time skip keyboard creation"""
        keyboard = KeyboardFactory.create_time_skip_keyboard()
        
        self.assertIsInstance(keyboard, InlineKeyboardMarkup)
        self.assertEqual(len(keyboard.inline_keyboard), 1)
        self.assertEqual(len(keyboard.inline_keyboard[0]), 1)
        
        button = keyboard.inline_keyboard[0][0]
        self.assertIn("Skip", button.text)
        self.assertEqual(button.callback_data, "time_skip")
    
    def test_get_location_by_index(self):
        """Test getting location by index"""
        # Valid indices
        self.assertEqual(KeyboardFactory.get_location_by_index(0), LOCATIONS[0])
        self.assertEqual(KeyboardFactory.get_location_by_index(1), LOCATIONS[1])
        
        # Invalid indices
        self.assertIsNone(KeyboardFactory.get_location_by_index(-1))
        self.assertIsNone(KeyboardFactory.get_location_by_index(len(LOCATIONS)))
        self.assertIsNone(KeyboardFactory.get_location_by_index(999))
    
    def test_get_friend_by_index(self):
        """Test getting friend by index"""
        # Valid indices
        self.assertEqual(KeyboardFactory.get_friend_by_index(0), FRIENDS[0])
        self.assertEqual(KeyboardFactory.get_friend_by_index(1), FRIENDS[1])
        
        # Invalid indices
        self.assertIsNone(KeyboardFactory.get_friend_by_index(-1))
        self.assertIsNone(KeyboardFactory.get_friend_by_index(len(FRIENDS)))
        self.assertIsNone(KeyboardFactory.get_friend_by_index(999))
    
    def test_parse_callback_data(self):
        """Test parsing callback data"""
        # Location callbacks
        action, param = KeyboardFactory.parse_callback_data(f"{CALLBACK_LOCATION}0")
        self.assertEqual(action, "location")
        self.assertEqual(param, "0")
        
        action, param = KeyboardFactory.parse_callback_data(f"{CALLBACK_LOCATION}5")
        self.assertEqual(action, "location")
        self.assertEqual(param, "5")
        
        # Friend callbacks
        action, param = KeyboardFactory.parse_callback_data(f"{CALLBACK_FRIEND}2")
        self.assertEqual(action, "friend")
        self.assertEqual(param, "2")
        
        # Confirm callbacks
        action, param = KeyboardFactory.parse_callback_data(f"{CALLBACK_CONFIRM}yes")
        self.assertEqual(action, "confirm")
        self.assertEqual(param, "yes")
        
        action, param = KeyboardFactory.parse_callback_data(f"{CALLBACK_CONFIRM}send")
        self.assertEqual(action, "confirm")
        self.assertEqual(param, "send")
        
        # Time skip
        action, param = KeyboardFactory.parse_callback_data("time_skip")
        self.assertEqual(action, "time_skip")
        self.assertIsNone(param)
        
        # Unknown callback
        action, param = KeyboardFactory.parse_callback_data("unknown_callback")
        self.assertEqual(action, "unknown")
        self.assertEqual(param, "unknown_callback")
    
    def test_create_custom_keyboard(self):
        """Test creating custom keyboard"""
        button_specs = [
            [("Button 1", "callback1"), ("Button 2", "callback2")],
            [("Button 3", "callback3")]
        ]
        
        keyboard = KeyboardFactory.create_custom_keyboard(button_specs)
        
        self.assertIsInstance(keyboard, InlineKeyboardMarkup)
        self.assertEqual(len(keyboard.inline_keyboard), 2)
        
        # First row
        first_row = keyboard.inline_keyboard[0]
        self.assertEqual(len(first_row), 2)
        self.assertEqual(first_row[0].text, "Button 1")
        self.assertEqual(first_row[0].callback_data, "callback1")
        self.assertEqual(first_row[1].text, "Button 2")
        self.assertEqual(first_row[1].callback_data, "callback2")
        
        # Second row
        second_row = keyboard.inline_keyboard[1]
        self.assertEqual(len(second_row), 1)
        self.assertEqual(second_row[0].text, "Button 3")
        self.assertEqual(second_row[0].callback_data, "callback3")
    
    def test_get_available_locations(self):
        """Test getting available locations"""
        locations = KeyboardFactory.get_available_locations()
        
        self.assertEqual(locations, LOCATIONS)
        # Should be a copy, not the original
        locations.append("New Location")
        self.assertNotEqual(locations, LOCATIONS)
    
    def test_get_available_friends(self):
        """Test getting available friends"""
        friends = KeyboardFactory.get_available_friends()
        
        self.assertEqual(friends, FRIENDS)
        # Should be a copy, not the original
        friends.append("New Friend")
        self.assertNotEqual(friends, FRIENDS)
    
    def test_friends_keyboard_callback_data(self):
        """Test that friends keyboard has correct callback data"""
        keyboard = KeyboardFactory.create_friends_keyboard(self.session)
        
        # Check friend button callback data
        friend_index = 0
        for row in keyboard.inline_keyboard[:-1]:  # Exclude action row
            for button in row:
                expected_callback = f"{CALLBACK_FRIEND}{friend_index}"
                self.assertEqual(button.callback_data, expected_callback)
                friend_index += 1
    
    def test_location_keyboard_layout(self):
        """Test location keyboard layout (2 buttons per row)"""
        keyboard = KeyboardFactory.create_location_keyboard()
        
        # Most rows should have 2 buttons (except possibly the last one)
        for i, row in enumerate(keyboard.inline_keyboard[:-1]):
            self.assertEqual(len(row), 2, f"Row {i} should have 2 buttons")
        
        # Last row might have 1 or 2 buttons depending on total count
        last_row = keyboard.inline_keyboard[-1]
        self.assertIn(len(last_row), [1, 2], "Last row should have 1 or 2 buttons")


if __name__ == "__main__":
    unittest.main()