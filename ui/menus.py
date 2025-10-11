"""
Menu system for the 3D Hunting Simulator.
Handles main menu, pause menu, game over screen, and other UI menus.
"""

from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DirectEntry, DirectSlider,
    DirectCheckButton, DirectOptionMenu
)
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TextNode, Vec4, Vec3, Point3, TransparencyAttrib
from typing import Callable, Optional, Dict, Any
import sys


class BaseMenu:
    """Base class for all menu screens."""

    def __init__(self, app, title: str = ""):
        self.app = app
        self.title = title
        self.frame = None
        self.elements = []
        self.visible = False

        # Menu colors and styling
        self.bg_color = (0.1, 0.1, 0.1, 0.9)
        self.button_color = (0.2, 0.4, 0.6, 1)
        self.button_hover_color = (0.3, 0.5, 0.7, 1)
        self.text_color = (1, 1, 1, 1)

    def create_frame(self, width: float = 1.0, height: float = 1.0):
        """Create the main menu frame."""
        self.frame = DirectFrame(
            frameColor=self.bg_color,
            frameSize=(-width/2, width/2, -height/2, height/2),
            pos=(0, 0, 0)
        )
        self.frame.hide()  # Start hidden

    def add_title(self, text: str, scale: float = 0.15, pos: tuple = (0, 0, 0.7)):
        """Add a title to the menu."""
        title = OnscreenText(
            text=text,
            pos=pos,
            scale=scale,
            fg=self.text_color,
            align=TextNode.ACenter
        )
        # Set font only if loader is available
        if hasattr(self.app, 'loader') and hasattr(self.app.loader, 'loadFont'):
            try:
                title.setFont(self.app.loader.loadFont("cmss12"))
            except:
                pass  # Use default font if cmss12 not available
        self.elements.append(title)
        return title

    def add_button(self, text: str, command: Callable, pos: tuple = (0, 0, 0),
                   scale: float = 0.1, extra_args: list = None):
        """Add a button to the menu."""
        button = DirectButton(
            text=text,
            command=command,
            extraArgs=extra_args or [],
            pos=pos,
            scale=scale,
            text_fg=self.text_color,
            frameColor=self.button_color,
            frameSize=(-0.3, 0.3, -0.05, 0.05),
            relief=1,
            pressEffect=1
        )
        button.setTransparency(TransparencyAttrib.MAlpha)

        # Add hover effect with proper closure
        def on_hover(*args):
            if hasattr(self, 'button_hover_color'):
                button['frameColor'] = self.button_hover_color
        def on_leave(*args):
            if hasattr(self, 'button_color'):
                button['frameColor'] = self.button_color

        # Store callbacks as attributes for re-binding if needed
        button.on_hover = on_hover
        button.on_leave = on_leave
        
        button.bind('rollover', on_hover)
        button.bind('rolloverExit', on_leave)

        self.elements.append(button)
        return button

    def add_label(self, text: str, pos: tuple = (0, 0, 0), scale: float = 0.08):
        """Add a text label to the menu."""
        label = OnscreenText(
            text=text,
            pos=pos,
            scale=scale,
            fg=self.text_color,
            align=TextNode.ACenter
        )
        # Set font only if loader is available
        if hasattr(self.app, 'loader') and hasattr(self.app.loader, 'loadFont'):
            try:
                label.setFont(self.app.loader.loadFont("cmss12"))
            except:
                pass  # Use default font if cmss12 not available
        self.elements.append(label)
        return label

    def show(self):
        """Show the menu."""
        if self.frame:
            self.frame.show()
        for element in self.elements:
            if hasattr(element, 'show'):
                element.show()
        self.visible = True

    def hide(self):
        """Hide the menu."""
        if self.frame:
            self.frame.hide()
        for element in self.elements:
            if hasattr(element, 'hide'):
                element.hide()
        self.visible = False

    def cleanup(self):
        """Clean up menu resources."""
        for element in self.elements:
            if hasattr(element, 'destroy'):
                element.destroy()
        if self.frame:
            self.frame.destroy()
        self.elements.clear()


class MainMenu(BaseMenu):
    """Main menu screen for the game."""

    def __init__(self, app, on_start_game: Callable, on_settings: Callable, on_quit: Callable):
        super().__init__(app, "3D Hunting Simulator")
        self.on_start_game = on_start_game
        self.on_settings = on_settings
        self.on_quit = on_quit

        self.create_main_menu()

    def create_main_menu(self):
        """Create the main menu layout."""
        self.create_frame(1.2, 1.0)

        # Title
        self.add_title("3D Hunting Simulator", scale=0.2, pos=(0, 0, 0.6))

        # Subtitle
        self.add_label("Experience the thrill of the hunt", pos=(0, 0, 0.4), scale=0.06)

        # Menu buttons
        y_pos = 0.2
        button_spacing = 0.15

        self.add_button(
            "Start Game",
            self.on_start_game,
            pos=(0, 0, y_pos),
            scale=0.12
        )

        y_pos -= button_spacing
        self.add_button(
            "Settings",
            self.on_settings,
            pos=(0, 0, y_pos),
            scale=0.12
        )

        y_pos -= button_spacing
        self.add_button(
            "Quit Game",
            self.on_quit,
            pos=(0, 0, y_pos),
            scale=0.12
        )

        # Version info
        self.add_label("Version 1.0", pos=(0, 0, -0.4), scale=0.04)


class PauseMenu(BaseMenu):
    """Pause menu screen."""

    def __init__(self, app, on_resume: Callable, on_restart: Callable, on_main_menu: Callable, on_quit: Callable):
        super().__init__(app, "Paused")
        self.on_resume = on_resume
        self.on_restart = on_restart
        self.on_main_menu = on_main_menu
        self.on_quit = on_quit

        self.create_pause_menu()

    def create_pause_menu(self):
        """Create the pause menu layout."""
        self.create_frame(0.8, 0.6)

        # Title
        self.add_title("Game Paused", scale=0.15, pos=(0, 0, 0.3))

        # Menu buttons
        y_pos = 0.1
        button_spacing = 0.12

        self.add_button(
            "Resume",
            self.on_resume,
            pos=(0, 0, y_pos),
            scale=0.1
        )

        y_pos -= button_spacing
        self.add_button(
            "Restart",
            self.on_restart,
            pos=(0, 0, y_pos),
            scale=0.1
        )

        y_pos -= button_spacing
        self.add_button(
            "Main Menu",
            self.on_main_menu,
            pos=(0, 0, y_pos),
            scale=0.1
        )

        y_pos -= button_spacing
        self.add_button(
            "Quit Game",
            self.on_quit,
            pos=(0, 0, y_pos),
            scale=0.1
        )


class GameOverMenu(BaseMenu):
    """Game over screen with score display."""

    def __init__(self, app, on_restart: Callable, on_main_menu: Callable, on_quit: Callable):
        super().__init__(app, "Game Over")
        self.on_restart = on_restart
        self.on_main_menu = on_main_menu
        self.on_quit = on_quit
        self.score = 0
        self.kills = 0
        self.accuracy = 0.0

        self.create_game_over_menu()

    def create_game_over_menu(self):
        """Create the game over menu layout."""
        self.create_frame(1.0, 0.8)

        # Title
        self.add_title("Game Over", scale=0.18, pos=(0, 0, 0.4))

        # Score display
        self.score_label = self.add_label("Score: 0", pos=(0, 0, 0.2), scale=0.1)
        self.kills_label = self.add_label("Kills: 0", pos=(0, 0, 0.1), scale=0.08)
        self.accuracy_label = self.add_label("Accuracy: 0%", pos=(0, 0, 0.0), scale=0.08)

        # Menu buttons
        y_pos = -0.15
        button_spacing = 0.12

        self.add_button(
            "Play Again",
            self.on_restart,
            pos=(0, 0, y_pos),
            scale=0.1
        )

        y_pos -= button_spacing
        self.add_button(
            "Main Menu",
            self.on_main_menu,
            pos=(0, 0, y_pos),
            scale=0.1
        )

        y_pos -= button_spacing
        self.add_button(
            "Quit Game",
            self.on_quit,
            pos=(0, 0, y_pos),
            scale=0.1
        )

    def update_score(self, score: int, kills: int, accuracy: float):
        """Update the displayed score information."""
        self.score = score
        self.kills = kills
        self.accuracy = accuracy

        if hasattr(self, 'score_label'):
            self.score_label.setText(f"Score: {score}")
        if hasattr(self, 'kills_label'):
            self.kills_label.setText(f"Kills: {kills}")
        if hasattr(self, 'accuracy_label'):
            self.accuracy_label.setText(f"Accuracy: {accuracy:.1f}%")


class SettingsMenu(BaseMenu):
    """Settings menu for game configuration."""

    def __init__(self, app, on_back: Callable, settings: Dict[str, Any] = None):
        super().__init__(app, "Settings")
        self.on_back = on_back
        self.settings = settings or {}
        self.sliders = {}
        self.check_buttons = {}

        self.create_settings_menu()

    def create_settings_menu(self):
        """Create the settings menu layout."""
        self.create_frame(1.0, 0.9)

        # Title
        self.add_title("Settings", scale=0.15, pos=(0, 0, 0.4))

        # Settings options
        y_pos = 0.2
        spacing = 0.15

        # Volume slider
        self.add_label("Master Volume", pos=(-0.3, 0, y_pos), scale=0.07)
        self.sliders['volume'] = DirectSlider(
            pos=(0.2, 0, y_pos),
            scale=0.3,
            value=self.settings.get('volume', 0.8),
            range=(0, 1),
            frameSize=(-0.5, 0.5, -0.02, 0.02),
            command=self._on_volume_change,
            extraArgs=['volume']
        )

        y_pos -= spacing
        # Mouse sensitivity slider
        self.add_label("Mouse Sensitivity", pos=(-0.3, 0, y_pos), scale=0.07)
        self.sliders['sensitivity'] = DirectSlider(
            pos=(0.2, 0, y_pos),
            scale=0.3,
            value=self.settings.get('sensitivity', 0.2),
            range=(0.1, 1.0),
            frameSize=(-0.5, 0.5, -0.02, 0.02),
            command=self._on_sensitivity_change,
            extraArgs=['sensitivity']
        )

        y_pos -= spacing
        # Fullscreen checkbox
        self.check_buttons['fullscreen'] = DirectCheckButton(
            text="Fullscreen",
            pos=(-0.3, 0, y_pos),
            scale=0.08,
            indicatorValue=self.settings.get('fullscreen', False),
            command=self._on_fullscreen_toggle,
            extraArgs=['fullscreen']
        )

        y_pos -= spacing
        # VSync checkbox
        self.check_buttons['vsync'] = DirectCheckButton(
            text="VSync",
            pos=(-0.3, 0, y_pos),
            scale=0.08,
            indicatorValue=self.settings.get('vsync', True),
            command=self._on_vsync_toggle,
            extraArgs=['vsync']
        )

        # Back button
        self.add_button(
            "Back",
            self._on_settings_back,
            pos=(0, 0, -0.3),
            scale=0.1
        )

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings from UI elements."""
        settings = {}
        for key, slider in self.sliders.items():
            settings[key] = slider['value']
        for key, checkbox in self.check_buttons.items():
            settings[key] = checkbox['indicatorValue']
        return settings

    def _on_fullscreen_toggle(self, setting_name):
        """Handle fullscreen toggle from checkbox."""
        current_value = self.check_buttons[setting_name].indicatorValue
        self.settings[setting_name] = current_value
        print(f"{setting_name} toggle: {current_value}")
        
        # Apply fullscreen setting immediately if possible
        if hasattr(self.app, 'win') and hasattr(self.app.win, 'getProperties'):
            try:
                if hasattr(self.app, 'win'):
                    from panda3d.core import WindowProperties
                    props = WindowProperties()
                    props.setFullscreen(current_value)
                    self.app.win.requestProperties(props)
                    print(f"Fullscreen set to: {current_value}")
            except Exception as e:
                print(f"Failed to set fullscreen: {e}")

    def _on_vsync_toggle(self, setting_name):
        """Handle VSync toggle from checkbox."""
        current_value = self.check_buttons[setting_name].indicatorValue
        self.settings[setting_name] = current_value
        print(f"{setting_name} toggle: {current_value}")

        # Apply VSync setting immediately if possible
        if hasattr(self.app, 'setFrameSync'):
            try:
                self.app.setFrameSync(current_value)
                print(f"VSync set to: {current_value}")
            except Exception as e:
                print(f"Failed to set VSync: {e}")

    def _on_settings_back(self):
        """Handle back button - apply all settings before going back."""
        # Apply all settings when going back
        self._apply_all_settings()
        # Call the original back callback
        if hasattr(self, 'on_back') and callable(self.on_back):
            self.on_back()

    def _apply_all_settings(self):
        """Apply all current settings to the game."""
        # Get current values from UI elements
        for key, slider in self.sliders.items():
            self.settings[key] = slider['value']
        for key, checkbox in self.check_buttons.items():
            self.settings[key] = checkbox.indicatorValue
            
        print(f"Settings applied: {self.settings}")
        
        # Apply settings immediately
        if 'fullscreen' in self.settings:
            self._on_fullscreen_toggle('fullscreen')
        if 'vsync' in self.settings:
            self._on_vsync_toggle('vsync')
        if 'volume' in self.settings:
            self._on_volume_change()
        if 'sensitivity' in self.settings:
            self._on_sensitivity_change()

    def _on_volume_change(self, *args, setting_name=None):
        """Handle volume changes."""
        if setting_name is not None:
            # Get value from slider
            slider_value = self.sliders[setting_name]['value']
            self.settings[setting_name] = slider_value
        else:
            # Get from settings dict
            slider_value = self.settings.get('volume', 0.8)
        print(f"Volume set to: {slider_value}")
        
    def _on_sensitivity_change(self, *args, setting_name=None):
        """Handle sensitivity changes."""
        if setting_name is not None:
            # Get value from slider
            slider_value = self.sliders[setting_name]['value']
            self.settings[setting_name] = slider_value
        else:
            # Get from settings dict
            slider_value = self.settings.get('sensitivity', 0.2)
        print(f"Mouse sensitivity set to: {slider_value}")
        
        # Update player sensitivity if possible
        # This would need to be connected to the game in a real implementation


class UIManager:
    """Manager class for all UI menus and HUD."""

    def __init__(self, app):
        self.app = app
        self.hud = None
        self.main_menu = None
        self.pause_menu = None
        self.game_over_menu = None
        self.settings_menu = None
        self.current_menu = None

        # Game state callbacks
        self.callbacks = {}

    def setup_hud(self, player):
        """Set up the HUD system."""
        from .hud import HUD
        self.hud = HUD(self.app, player)

    def setup_menus(self, callbacks: Dict[str, Callable]):
        """Set up all menu screens with callbacks."""
        self.callbacks = callbacks

        # Create menus
        self.main_menu = MainMenu(
            self.app,
            callbacks.get('start_game', lambda: None),
            callbacks.get('settings', lambda: None),
            callbacks.get('quit', lambda: None)
        )

        self.pause_menu = PauseMenu(
            self.app,
            callbacks.get('resume', lambda: None),
            callbacks.get('restart', lambda: None),
            callbacks.get('main_menu', lambda: None),
            callbacks.get('quit', lambda: None)
        )

        self.game_over_menu = GameOverMenu(
            self.app,
            callbacks.get('restart', lambda: None),
            callbacks.get('main_menu', lambda: None),
            callbacks.get('quit', lambda: None)
        )

        self.settings_menu = SettingsMenu(
            self.app,
            callbacks.get('back_to_main', lambda: None),
            callbacks.get('settings_data', {})
        )

    def show_menu(self, menu_type: str):
        """Show a specific menu and hide others."""
        # Hide current menu
        if self.current_menu:
            self.current_menu.hide()

        # Show requested menu
        if menu_type == 'main':
            self.current_menu = self.main_menu
        elif menu_type == 'pause':
            self.current_menu = self.pause_menu
        elif menu_type == 'game_over':
            self.current_menu = self.game_over_menu
        elif menu_type == 'settings':
            self.current_menu = self.settings_menu

        if self.current_menu:
            self.current_menu.show()

    def hide_menus(self):
        """Hide all menus."""
        if self.current_menu:
            self.current_menu.hide()
            self.current_menu = None

    def update_hud(self, dt: float):
        """Update HUD elements."""
        if self.hud:
            self.hud.update(dt)

    def update_game_over_score(self, score: int, kills: int, accuracy: float):
        """Update game over screen with final score."""
        if self.game_over_menu:
            self.game_over_menu.update_score(score, kills, accuracy)

    def toggle_hud_visibility(self, visible: bool = True):
        """Toggle HUD visibility."""
        if self.hud:
            self.hud.toggle_visibility(visible)

    def add_score(self, points: int):
        """Add points to HUD score."""
        if self.hud:
            self.hud.add_score(points)

    def record_shot(self, hit: bool = False):
        """Record a shot in HUD statistics."""
        if self.hud:
            self.hud.record_shot(hit)

    def show_message(self, message: str, duration: float = 3.0):
        """Show a temporary message on HUD."""
        if self.hud:
            self.hud.show_message(message, duration)

    def cleanup(self):
        """Clean up all UI resources."""
        if self.hud:
            self.hud.cleanup()

        menus = [self.main_menu, self.pause_menu, self.game_over_menu, self.settings_menu]
        for menu in menus:
            if menu:
                menu.cleanup()