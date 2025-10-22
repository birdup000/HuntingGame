#!/usr/bin/env python3
"""
Targeted tests for specific missing coverage lines in core modules.
Focused on achievable 100% coverage for key statements.
"""

import sys
import unittest
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, '.')

class TargetedCoverageTests(unittest.TestCase):
    """Highly targeted tests for specific missing coverage lines."""

    def test_game_dynamic_lighting_coverage(self):
        """Test dynamic lighting functionality in game."""
        try:
            from core.game import Game
            
            # Create mock app with render
            mock_app = Mock()
            mock_app.render = Mock()
            mock_app.taskMgr = Mock()
            mock_app.taskMgr.add = Mock()
            mock_app.win = None  # Test path where win is None
            
            # Patch dynamic lighting to be available
            with patch('core.game.DynamicLighting') as mock_dyn_light:
                mock_dyn_light_instance = Mock()
                mock_dyn_light.return_value = mock_dyn_light_instance
                
                # Create game - this should exercise init paths
                game = Game(mock_app)
                
                # Test that dynamic lighting was initialized
                self.assertIsNotNone(game.dynamic_lighting)
                
                # Test toggle debug lights
                game.toggle_debug_lights()
                mock_dyn_light_instance.toggle_debug_lights.assert_called()
                
        except Exception as e:
            self.fail(f"Dynamic lighting coverage test failed: {e}")

    def test_game_weather_system_coverage(self):
        """Test weather system functionality in game."""
        try:
            from core.game import Game
            
            # Create mock app
            mock_app = Mock()
            mock_app.render = Mock()
            mock_app.taskMgr = Mock()
            mock_app.taskMgr.add = Mock()
            
            with patch('core.game.WeatherSystem') as mock_weather:
                mock_weather_instance = Mock()
                mock_weather.return_value = mock_weather_instance
                
                game = Game(mock_app)
                
                # Test that weather system was initialized
                self.assertIsNotNone(game.weather_system)
                
        except Exception as e:
            self.fail(f"Weather system coverage test failed: {e}")

    def test_game_escape_handling(self):
        """Test escape key handling."""
        try:
            from core.game import Game
            
            # Create mock app
            mock_app = Mock()
            mock_app.render = Mock()
            mock_app.taskMgr = Mock()
            mock_app.taskMgr.add = Mock()
            
            with patch('core.game.UIManager') as mock_ui_manager:
                mock_ui = Mock()
                mock_ui_manager.return_value = mock_ui
                
                game = Game(mock_app)
                
                # Test escape in playing state
                game.game_state = 'playing'
                game.handle_escape()
                self.assertEqual(game.game_state, 'paused')  # pause_game should be called
                
                # Test escape in paused state  
                game.game_state = 'paused'
                game.handle_escape()
                self.assertEqual(game.game_state, 'playing')  # resume_game should be called
                
        except Exception as e:
            self.fail(f"Escape handling coverage test failed: {e}")

    def test_player_cursor_control_with_win(self):
        """Test cursor control with window object."""
        try:
            from core.game import Game
            
            # Create mock app with win object
            mock_app = Mock()
            mock_app.render = Mock()
            mock_app.taskMgr = Mock()
            mock_app.taskMgr.add = Mock()
            mock_app.openPointer = Mock()
            mock_app.win = Mock()
            mock_app.win.get_properties = Mock()
            
            # Create window properties mock
            mock_props = Mock()
            mock_props.set_cursor_hidden = Mock()
            mock_app.win.get_properties.return_value = mock_props
            mock_app.win.request_properties = Mock()
            
            with patch('core.game.UIManager') as mock_ui_manager:
                with patch('core.game.Player') as mock_player:
                    mock_ui = Mock()
                    mock_player_instance = Mock()
                    mock_player.return_value = mock_player_instance
                    mock_ui_manager.return_value = mock_ui
                    
                    game = Game(mock_app)
                    
                    # Test start_gameplay which has cursor control logic
                    game.start_gameplay()
                    
                    # Verify openPointer was called to hide cursor
                    mock_app.openPointer.assert_called_with(0)
                    
        except Exception as e:
            self.fail(f"Cursor control coverage test failed: {e}")

    def test_player_cursor_control_with_properties(self):
        """Test cursor control with properties fallback."""
        try:
            from core.game import Game
            
            # Create mock app without openPointer but with win
            mock_app = Mock()
            mock_app.render = Mock()
            mock_app.taskMgr = Mock()
            mock_app.taskMgr.add = Mock()
            mock_app.win = Mock()
            mock_app.win.get_properties = Mock()
            
            # Remove openPointer attribute to test fallback
            del mock_app.openPointer
            
            # Create window properties mock
            mock_props = Mock()
            mock_props.set_cursor_hidden = Mock()
            mock_app.win.get_properties.return_value = mock_props
            mock_app.win.request_properties = Mock()
            
            # Mock the UI setup
            with patch('core.game.UIManager') as mock_ui_manager:
                with patch('core.game.Player') as mock_player:
                    mock_player_instance = Mock()
                    mock_player_instance.adjust_to_terrain = Mock()
                    mock_player.return_value = mock_player_instance
                    
                    mock_ui = Mock()
                    mock_ui.hide_menus = Mock()
                    mock_ui.setup_hud = Mock()
                    mock_ui.toggle_hud_visibility = Mock()
                    mock_ui_manager.return_value = mock_ui
                    
                    game = Game(mock_app)
                    
                    # Test start_gameplay which should use properties fallback
                    game.start_gameplay()
                    
                    # Verify win properties methods were called
                    mock_app.win.get_properties.assert_called()
                    mock_props.set_cursor_hidden.assert_called_with(True)
                    mock_app.win.request_properties.assert_called_with(mock_props)
                    
        except Exception as e:
            self.fail(f"Cursor control with properties coverage test failed: {e}")

    def test_player_cursor_control_failure(self):
        """Test cursor control when both methods fail."""
        try:
            from core.game import Game
            
            # Create mock app where both cursor methods fail
            mock_app = Mock()
            mock_app.render = Mock()
            mock_app.taskMgr = Mock()
            mock_app.taskMgr.add = Mock()
            mock_app.win = Mock()
            mock_app.win.get_properties = Mock(side_effect=Exception("Properties failed"))
            
            # Remove openPointer attribute
            del mock_app.openPointer
            
            # Mock the UI setup
            with patch('core.game.UIManager') as mock_ui_manager:
                with patch('core.game.Player') as mock_player:
                    mock_player_instance = Mock()
                    mock_player_instance.adjust_to_terrain = Mock()
                    mock_player.return_value = mock_player_instance
                    
                    mock_ui = Mock()
                    mock_ui.hide_menus = Mock()
                    mock_ui.setup_hud = Mock()
                    mock_ui.toggle_hud_visibility = Mock()
                    mock_ui_manager.return_value = mock_ui
                    
                    game = Game(mock_app)
                    
                    # This should not crash even when properties fail
                    game.start_gameplay()
                    
        except Exception as e:
            self.fail(f"Cursor control failure coverage test failed: {e}")

    def test_environment_cleanup_edge_cases(self):
        """Test environment cleanup with edge cases."""
        try:
            from core.game import Game
            
            # Create mock app
            mock_app = Mock()
            mock_app.render = Mock()
            mock_app.taskMgr = Mock()
            mock_app.taskMgr.add = Mock()
            
            with patch('core.game.UIManager') as mock_ui_manager:
                game = Game(mock_app)
                
                # Test cleanup with None objects
                game.stop()
                
        except Exception as e:
            self.fail(f"Environment cleanup edge cases coverage test failed: {e}")

    def test_game_update_playing_state(self):
        """Test game update in playing state."""
        try:
            from core.game import Game
            
            # Create mock app
            mock_app = Mock()
            mock_app.render = Mock()
            mock_app.taskMgr = Mock()
            mock_app.taskMgr.globalClock = Mock()
            mock_app.taskMgr.globalClock.getFrameTime = Mock(return_value=0.016)
            
            with patch('core.game.UIManager') as mock_ui_manager:
                with patch('core.game.Player') as mock_player:
                    with patch('core.game.PBRTerrain') as mock_terrain:
                        mock_player_instance = Mock()
                        mock_player_instance.update = Mock()
                        mock_player.return_value = mock_player_instance
                        
                        mock_terrain_instance = Mock()
                        mock_terrain_instance.get_height = Mock(return_value=0.0)
                        mock_terrain.return_value = mock_terrain_instance
                        
                        mock_ui = Mock()
                        mock_ui.update_hud = Mock()
                        mock_ui_manager.return_value = mock_ui
                        
                        game = Game(mock_app)
                        
                        # Set up for playing state
                        game.game_state = 'playing'
                        game.player = mock_player_instance
                        game.terrain = mock_terrain_instance
                        game.ui_manager = mock_ui
                        game.is_running = True
                        
                        # Mock task for update
                        mock_task = Mock()
                        
                        # This should test the playing state update path
                        result = game.update(mock_task)
                        
                        # Should continue the update loop
                        self.assertEqual(result, mock_task.cont)
                        
        except Exception as e:
            self.fail(f"Game update playing state coverage test failed: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
