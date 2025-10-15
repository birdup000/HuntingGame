"""
Menu system for the 3D Hunting Simulator.
Handles main menu, pause menu, game over screen, and other UI menus.
"""

from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectSlider,
    DirectCheckButton
)
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
import os
from panda3d.core import TextNode, TransparencyAttrib, Texture, PNMImage, Filename
from typing import Callable, Optional, Dict, Any, Tuple


class BaseMenu:
    """Base class for all menu screens."""

    _shared_font = None
    _font_checked = False

    def __init__(self, app, title: str = ""):
        self.app = app
        self.title = title
        self.frame = None
        self.background = None
        self.elements = []
        self.borders = []  # Initialize borders list
        self.visible = False
        self.selected_button = None  # For accessibility

        self.bg_color = (0.07, 0.1, 0.12, 0.92)
        self.button_color = (0.12, 0.22, 0.14, 0.95)  # Forest green
        self.button_hover_color = (0.18, 0.32, 0.2, 0.95)  # Lighter forest green
        self.button_selected_color = (0.35, 0.6, 0.3, 1.0)  # Accent green for selection
        self.text_color = (0.94, 0.96, 0.9, 1.0)  # Slightly off-white
        self.title_color = (0.98, 0.92, 0.7, 1.0)  # Golden accent for titles
        self.border_color = (0.6, 0.5, 0.3, 0.7)  # Earth brown
        self.selection_text_color = (0.98, 0.94, 0.75, 1.0)  # Golden glow for selection

    def _get_ui_font(self):
        """Return a shared UI font if a bundled font exists, else default."""
        if BaseMenu._shared_font is not None:
            return BaseMenu._shared_font
        if not BaseMenu._font_checked:
            BaseMenu._font_checked = True
            font_dir = os.path.join(os.path.dirname(__file__), '..', 'fonts')
            candidate = os.path.join(font_dir, 'ui_font.ttf')
            if hasattr(self.app, 'loader') and hasattr(self.app.loader, 'loadFont') and os.path.isfile(candidate):
                try:
                    filename = Filename.fromOsSpecific(candidate)
                    BaseMenu._shared_font = self.app.loader.loadFont(filename)
                except Exception:
                    BaseMenu._shared_font = None
        if BaseMenu._shared_font is None:
            BaseMenu._shared_font = TextNode.getDefaultFont()
        return BaseMenu._shared_font

    def create_frame(self, width: float = 1.0, height: float = 1.0, frame_color: Optional[Tuple[float, float, float, float]] = None):
        """Create the main menu frame with optional background."""
        parent = getattr(self.app, 'aspect2d', getattr(self.app, 'render2d', None))
        if parent is None:
            raise RuntimeError("UI menus require an app with aspect2d or render2d")

        if not self.background:
            left, right, bottom, top = self._get_fullscreen_frame_size()
            self.background = DirectFrame(
                parent=parent,
                frameColor=(1.0, 1.0, 1.0, 1.0),
                frameSize=(left, right, bottom, top),
                sortOrder=0
            )
            self.background.setTransparency(TransparencyAttrib.MAlpha)
            self.background.hide()
            self._ensure_background_visuals()

        if self.frame:
            self.frame.destroy()

        content_parent = getattr(self, '_background_tint', self.background)
        self.frame = DirectFrame(
            frameColor=frame_color if frame_color is not None else self.bg_color,
            frameSize=(-width / 2, width / 2, -height / 2, height / 2),
            pos=(0, 0, 0),
            parent=content_parent,
            sortOrder=1,
            borderWidth=(0.0, 0.0)
        )
        self.frame.setTransparency(TransparencyAttrib.MAlpha)
        self.frame.hide()

    def add_frame_border(self, frame, width, height):
        """Add a decorative border around the frame - simplified approach."""
        # Remove border functionality to prevent layering issues
        # Borders are handled by the main frame itself with better styling
        pass

    def add_title(self, text: str, scale: float = 0.15, pos: tuple = (0, 0, 0.7), parent=None,
                  fg: Optional[Tuple[float, float, float, float]] = None):
        """Add a title to the menu with proper positioning."""
        # Ensure we have a frame to parent to
        if not self.frame:
            self.create_frame()
        target_parent = parent or self.frame
        title = OnscreenText(
            text=text,
            pos=pos,
            scale=scale,
            fg=fg or self.title_color,
            align=TextNode.ACenter,
            parent=target_parent,
            mayChange=True,
            shadow=(0, 0, 0, 0.85),
            shadowOffset=(0.01, 0.01)
        )
        ui_font = self._get_ui_font()
        if ui_font:
            title.setFont(ui_font)
        self.elements.append(title)
        return title

    def add_button(self, text: str, command: Callable, pos: tuple = (0, 0, 0),
                   scale: float = 0.1, extra_args: list = None, is_primary: bool = False, parent=None):
        """Add a button to the menu with proper positioning and styling."""
        if not self.frame:
            self.create_frame()
        target_parent = parent or self.frame
        button = DirectButton(
            text=text,
            command=command,
            extraArgs=extra_args or [],
            parent=target_parent,
            pos=pos,
            scale=scale,
            text_fg=self.text_color,
            text_shadow=(0, 0, 0, 0.85),
            frameColor=self.button_color,
            frameSize=(-0.5, 0.5, -0.12, 0.12),
            relief=1,
            pressEffect=1,
            borderWidth=(0.02, 0.02),
            text_align=TextNode.ACenter,
            text_pos=(0, -0.03)
        )
        button.setTransparency(TransparencyAttrib.MAlpha)
        button.setPythonTag('activation_command', command)
        ui_font = self._get_ui_font()
        if ui_font:
            button['text_font'] = ui_font

        base_scale_vec = button.getScale()
        button._base_scale = base_scale_vec
        button._base_border_width = button['borderWidth']
        button._hover_scale = base_scale_vec * 1.05
        button._selected_scale = base_scale_vec * 1.15
        button._hover_border_width = tuple(width * 2 for width in button._base_border_width)
        button._selected_border_width = tuple(width * 3 for width in button._base_border_width)
        button._base_text = text

        def enhanced_hover(*args):
            if self.selected_button == button:
                return
            button['frameColor'] = self.button_hover_color
            button['borderWidth'] = getattr(button, '_hover_border_width', (0.04, 0.04))
            button['text_fg'] = self.selection_text_color
            hover_scale = getattr(button, '_hover_scale', None)
            if hover_scale is not None:
                button.setScale(hover_scale)
            else:
                button.setScale(scale * 1.05)

        def standard_leave(*args):
            if self.selected_button != button:
                button['frameColor'] = self.button_color
                button['borderWidth'] = getattr(button, '_base_border_width', (0.02, 0.02))
                button['text_fg'] = self.text_color
                base_scale = getattr(button, '_base_scale', None)
                if base_scale is not None:
                    button.setScale(base_scale)
                else:
                    button.setScale(scale)

        def enhanced_focus(*args):
            if hasattr(self, 'selected_button'):
                if self.selected_button and self.selected_button != button:
                    self._reset_button_visual(self.selected_button)
                self.selected_button = button
                self._highlight_button(button)

        button.on_hover = enhanced_hover
        button.on_leave = standard_leave
        button.on_focus = enhanced_focus

        button.bind('rollover', enhanced_hover)
        button.bind('rolloverExit', standard_leave)
        button.bind('focusIn', enhanced_focus)

        self.elements.append(button)
        return button

    def add_label(self, text: str, pos: tuple = (0, 0, 0), scale: float = 0.08, parent=None,
                  align: int = TextNode.ACenter, fg: Optional[Tuple[float, float, float, float]] = None):
        """Add a text label to the menu with proper positioning."""
        # Ensure we have a frame to parent to
        if not self.frame:
            self.create_frame()
        target_parent = parent or self.frame
        label = OnscreenText(
            text=text,
            pos=pos,
            scale=scale,
            fg=fg or self.text_color,
            align=align,
            parent=target_parent,
            mayChange=True,
            shadow=(0, 0, 0, 0.8),
            shadowOffset=(0.009, 0.009)
        )
        ui_font = self._get_ui_font()
        if ui_font:
            label.setFont(ui_font)
        self.elements.append(label)
        return label

    def _get_fullscreen_frame_size(self):
        left = getattr(self.app, 'a2dLeft', -1.3)
        right = getattr(self.app, 'a2dRight', 1.3)
        bottom = getattr(self.app, 'a2dBottom', -1.0)
        top = getattr(self.app, 'a2dTop', 1.0)
        return (left, right, bottom, top)

    def _ensure_background_visuals(self):
        """Create a thematic background gradient once and reuse it."""
        if not self.background:
            return

        if getattr(self, '_background_art', None) is None:
            try:
                texture = self._get_shared_gradient_texture()
                if texture:
                    left, right, bottom, top = self._get_fullscreen_frame_size()
                    width = right - left
                    height = top - bottom
                    self._background_art = OnscreenImage(
                        image=texture,
                        parent=self.background,
                        pos=(0, 0, 0)
                    )
                    self._background_art.setScale(width / 2, 1.0, height / 2)
                    self._background_art.setTransparency(TransparencyAttrib.MAlpha)
                    self._background_art.setBin("background", 0)
            except Exception:
                self.background['frameColor'] = (0.0, 0.0, 0.0, 0.85)

        if getattr(self, '_background_tint', None) is None:
            left, right, bottom, top = self._get_fullscreen_frame_size()
            self._background_tint = DirectFrame(
                parent=self.background,
                frameColor=(0.0, 0.0, 0.0, 0.38),
                frameSize=(left, right, bottom, top),
                sortOrder=-1
            )
            self._background_tint.setTransparency(TransparencyAttrib.MAlpha)

    @classmethod
    def _get_shared_gradient_texture(cls):
        """Cache a reusable gradient texture for the background."""
        texture = getattr(cls, '_shared_background_texture', None)
        if texture is None:
            cls._shared_background_texture = cls._generate_gradient_texture(
                top_color=(0.32, 0.43, 0.36),
                bottom_color=(0.05, 0.09, 0.13)
            )
            texture = cls._shared_background_texture
        return texture

    @staticmethod
    def _generate_gradient_texture(top_color: Tuple[float, float, float],
                                   bottom_color: Tuple[float, float, float],
                                   size: int = 512) -> Optional[Texture]:
        try:
            image = PNMImage(size, size)
            for y in range(size):
                blend = y / float(size - 1)
                r = top_color[0] * (1.0 - blend) + bottom_color[0] * blend
                g = top_color[1] * (1.0 - blend) + bottom_color[1] * blend
                b = top_color[2] * (1.0 - blend) + bottom_color[2] * blend
                for x in range(size):
                    image.setXel(x, y, r, g, b)

            texture = Texture("menu-background-gradient")
            texture.load(image)
            texture.setWrapU(Texture.WMClamp)
            texture.setWrapV(Texture.WMClamp)
            texture.setMagfilter(Texture.FTLinear)
            texture.setMinfilter(Texture.FTLinear)
            return texture
        except Exception:
            return None

    def _reset_button_visual(self, button: DirectButton):
        """Restore a button to its base visual state."""
        if not button:
            return
        button['frameColor'] = self.button_color
        button['borderWidth'] = getattr(button, '_base_border_width', (0.02, 0.02))
        button['text_fg'] = self.text_color
        base_scale = getattr(button, '_base_scale', None)
        if base_scale is not None:
            button.setScale(base_scale)
        else:
            current_scale = button.getScale() if hasattr(button, 'getScale') else None
            if hasattr(current_scale, 'x'):
                button.setScale(current_scale.x)
            elif isinstance(current_scale, tuple) and current_scale:
                button.setScale(current_scale[0])
            else:
                button.setScale(0.1)
        if hasattr(button, '_base_text'):
            button['text'] = button._base_text

    def _highlight_button(self, button: DirectButton):
        """Apply the selected styling to a button."""
        if not button:
            return
        button['frameColor'] = self.button_selected_color
        button['borderWidth'] = getattr(button, '_selected_border_width', (0.06, 0.06))
        button['text_fg'] = self.selection_text_color
        selected_scale = getattr(button, '_selected_scale', None)
        if selected_scale is not None:
            button.setScale(selected_scale)
        else:
            current_scale = button.getScale() if hasattr(button, 'getScale') else None
            if hasattr(current_scale, 'x'):
                button.setScale(current_scale.x * 1.15)
            elif isinstance(current_scale, tuple) and current_scale:
                button.setScale(current_scale[0] * 1.15)
            else:
                button.setScale(0.115)
        if hasattr(button, '_base_text'):
            button['text'] = button._base_text


    def show(self):
        """Show the menu."""
        if self.background:
            self.background.show()
        if self.frame:
            self.frame.show()
        # Show any borders
        if hasattr(self, 'borders'):
            for border in self.borders:
                border.show()
        for element in self.elements:
            if hasattr(element, 'show'):
                element.show()
        
        # Set initial focus if available
        self.setup_navigation()
        self.visible = True

    def setup_navigation(self):
        """Setup keyboard navigation for accessibility."""
        # Find all buttons in elements
        buttons = [elem for elem in self.elements if isinstance(elem, DirectButton)]
        if buttons:
            # Reset button visuals before applying selection
            for button in buttons:
                self._reset_button_visual(button)

            # Set focus on first button
            self.selected_button = buttons[0]
            self._highlight_button(self.selected_button)

            # Bind keyboard navigation in the app if not already bound
            if hasattr(self.app, 'accept') and hasattr(self.app, 'ignore'):
                # Only bind once - check if already bound
                if not hasattr(self, '_nav_bound'):
                    self.app.accept('arrow_up', self.select_previous)
                    self.app.accept('arrow_down', self.select_next)
                    self.app.accept('enter', self.activate_selection)
                    self._nav_bound = True
                    
                    # Change focus style to show selection
                    for button in buttons:
                        button.bind('focusIn', button.on_focus)
                            
    def select_previous(self):
        """Select the previous button with proper scaling."""
        buttons = [elem for elem in self.elements if isinstance(elem, DirectButton)]
        if not buttons:
            return

        if self.selected_button not in buttons:
            self.selected_button = buttons[0]

        if not self.selected_button:
            self.selected_button = buttons[0]
            self._highlight_button(self.selected_button)
            return

        try:
            current_idx = buttons.index(self.selected_button)
            new_idx = (current_idx - 1) % len(buttons)
            self._reset_button_visual(self.selected_button)
            self.selected_button = buttons[new_idx]
            self._highlight_button(self.selected_button)
        except (ValueError, IndexError):
            for button in buttons:
                self._reset_button_visual(button)
            self.selected_button = buttons[0]
            self._highlight_button(self.selected_button)

    def select_next(self):
        """Select the next button with proper scaling."""
        buttons = [elem for elem in self.elements if isinstance(elem, DirectButton)]
        if not buttons:
            return

        if self.selected_button not in buttons:
            self.selected_button = buttons[0]

        if not self.selected_button:
            self.selected_button = buttons[0]
            self._highlight_button(self.selected_button)
            return

        try:
            current_idx = buttons.index(self.selected_button)
            new_idx = (current_idx + 1) % len(buttons)
            self._reset_button_visual(self.selected_button)
            self.selected_button = buttons[new_idx]
            self._highlight_button(self.selected_button)
        except (ValueError, IndexError):
            for button in buttons:
                self._reset_button_visual(button)
            self.selected_button = buttons[0]
            self._highlight_button(self.selected_button)

    def activate_selection(self):
        """Activate the currently selected button."""
        if self.selected_button:
            command = self.selected_button.getPythonTag('activation_command')
            if not command:
                try:
                    command = self.selected_button['command']
                except Exception:
                    command = None

            if command:
                command(*getattr(self.selected_button, 'extraArgs', []))
            
    def hide(self):
        """Hide the menu."""
        if self.frame:
            self.frame.hide()
        if self.background:
            self.background.hide()
        # Hide any borders
        if hasattr(self, 'borders'):
            for border in self.borders:
                border.hide()
        for element in self.elements:
            if hasattr(element, 'hide'):
                element.hide()
                
        # Cleanup navigation bindings
        if hasattr(self, '_nav_bound'):
            if hasattr(self.app, 'ignore'):
                self.app.ignore('arrow_up')
                self.app.ignore('arrow_down') 
                self.app.ignore('enter')
            self._nav_bound = False
            
        self.visible = False
        self.selected_button = None

    def cleanup(self):
        """Clean up menu resources."""
        # Clean up borders first
        if hasattr(self, 'borders'):
            for border in self.borders:
                if hasattr(border, 'destroy'):
                    border.destroy()
            self.borders.clear()
            
        for element in self.elements:
            if hasattr(element, 'destroy'):
                element.destroy()
        if self.frame:
            self.frame.destroy()
            self.frame = None
        if self.background:
            self.background.destroy()
            self.background = None
        self.elements.clear()


class MainMenu(BaseMenu):
    """Main menu screen for the game."""

    def __init__(self, app, on_start_game: Callable, on_settings: Callable, on_quit: Callable):
        super().__init__(app, "3D Hunting Simulator")
        self.on_start_game = on_start_game
        self.on_settings = on_settings
        self.on_quit = on_quit
        self.button_panel = None

        self.create_main_menu()

    def create_main_menu(self):
        """Create the main menu layout with clear hierarchy and readability."""
        self.create_frame(2.3, 1.6, frame_color=(0.0, 0.0, 0.0, 0.0))

        self.add_title(
            "3D HUNTING SIMULATOR",
            scale=0.27,
            pos=(0, 0, 0.78),
            parent=self.frame,
            fg=(0.97, 0.92, 0.8, 1.0)
        )

        self.add_label(
            "Experience the thrill of the hunt",
            pos=(0, 0, 0.6),
            scale=0.1,
            parent=self.frame,
            fg=(0.9, 0.85, 0.76, 1.0)
        )

        accent_bar = DirectFrame(
            parent=self.frame,
            frameColor=(0.78, 0.58, 0.26, 0.82),
            frameSize=(-0.45, 0.45, -0.01, 0.01),
            pos=(0, 0, 0.52)
        )
        accent_bar.setTransparency(TransparencyAttrib.MAlpha)

        self.button_panel = DirectFrame(
            parent=self.frame,
            frameColor=(0.08, 0.13, 0.09, 0.78),
            frameSize=(-0.8, 0.8, -0.55, 0.25),
            pos=(0, 0, -0.05),
            borderWidth=(0.02, 0.02)
        )
        self.button_panel.setTransparency(TransparencyAttrib.MAlpha)

        y_start = 0.12
        button_spacing = 0.24

        self.add_button(
            "Start Game",
            self.on_start_game,
            pos=(0, 0, y_start),
            scale=0.125,
            is_primary=True,
            parent=self.button_panel
        )

        self.add_button(
            "Settings",
            self.on_settings,
            pos=(0, 0, y_start - button_spacing),
            scale=0.12,
            parent=self.button_panel
        )

        self.add_button(
            "Quit Game",
            self.on_quit,
            pos=(0, 0, y_start - (2 * button_spacing)),
            scale=0.12,
            parent=self.button_panel
        )

        left, right, bottom, _top = self._get_fullscreen_frame_size()
        version_x = right - 0.35
        version_z = bottom + 0.18
        self.add_label(
            "Version 1.0",
            pos=(version_x, 0, version_z),
            scale=0.06,
            parent=self.background,
            align=TextNode.ARight,
            fg=(0.78, 0.81, 0.77, 1.0)
        )


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
        """Create the pause menu layout with improved hierarchy."""
        self.create_frame(1.0, 1.0)  # Taller frame for better proportions

        # Title at top with more prominence
        self.add_title("Game Paused", scale=0.22, pos=(0, 0, 0.45))

        # Menu buttons with improved spacing and alignment
        y_start = 0.15
        button_spacing = 0.12

        self.add_button(
            "Resume",
            self.on_resume,
            pos=(0, 0, y_start),
            scale=0.1
        )

        self.add_button(
            "Restart",
            self.on_restart,
            pos=(0, 0, y_start - button_spacing),
            scale=0.1
        )

        self.add_button(
            "Main Menu",
            self.on_main_menu,
            pos=(0, 0, y_start - (2 * button_spacing)),
            scale=0.1
        )

        self.add_button(
            "Quit Game",
            self.on_quit,
            pos=(0, 0, y_start - (3 * button_spacing)),
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
        self.create_frame(1.2, 1.0)  # Larger frame for better presentation

        # Title
        self.add_title("Game Over", scale=0.22, pos=(0, 0, 0.4))

        # Score display with better spacing
        self.score_label = self.add_label("Score: 0", pos=(0, 0, 0.15), scale=0.12)
        self.kills_label = self.add_label("Kills: 0", pos=(0, 0, 0.02), scale=0.09)
        self.accuracy_label = self.add_label("Accuracy: 0%", pos=(0, 0, -0.1), scale=0.09)

        # Menu buttons
        y_start = -0.25
        button_spacing = 0.12

        self.add_button(
            "Play Again",
            self.on_restart,
            pos=(0, 0, y_start),
            scale=0.1
        )

        self.add_button(
            "Main Menu",
            self.on_main_menu,
            pos=(0, 0, y_start - button_spacing),
            scale=0.1
        )

        self.add_button(
            "Quit Game",
            self.on_quit,
            pos=(0, 0, y_start - (2 * button_spacing)),
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
        self.create_frame(1.2, 1.0)  # Larger frame for settings

        # Title - large and centered
        self.add_title("Settings", scale=0.22, pos=(0, 0, 0.4))

        # Settings options - better organized layout
        y_pos = 0.2
        spacing = 0.11

        # Volume slider
        self.add_label("Master Volume", pos=(-0.3, 0, y_pos), scale=0.08)
        self.sliders['volume'] = DirectSlider(
            pos=(0.2, 0, y_pos),
            scale=0.3,
            value=self.settings.get('volume', 0.8),
            range=(0, 1),
            frameSize=(-0.5, 0.5, -0.02, 0.02),
            command=self._on_volume_change,
            extraArgs=['volume']
        )
        self.sliders['volume'].reparentTo(self.frame)  # Parent to frame instead

        y_pos -= spacing
        # Mouse sensitivity slider
        self.add_label("Mouse Sensitivity", pos=(-0.3, 0, y_pos), scale=0.08)
        self.sliders['sensitivity'] = DirectSlider(
            pos=(0.2, 0, y_pos),
            scale=0.3,
            value=self.settings.get('sensitivity', 0.2),
            range=(0.1, 1.0),
            frameSize=(-0.5, 0.5, -0.02, 0.02),
            command=self._on_sensitivity_change,
            extraArgs=['sensitivity']
        )
        self.sliders['sensitivity'].reparentTo(self.frame)  # Parent to frame instead

        y_pos -= spacing
        # Fullscreen checkbox
        self.check_buttons['fullscreen'] = DirectCheckButton(
            text="Fullscreen",
            pos=(-0.3, 0, y_pos),
            scale=0.09,
            indicatorValue=self.settings.get('fullscreen', False),
            command=self._on_fullscreen_toggle,
            extraArgs=['fullscreen']
        )
        self.check_buttons['fullscreen'].reparentTo(self.frame)  # Parent to frame instead

        y_pos -= spacing
        # VSync checkbox
        self.check_buttons['vsync'] = DirectCheckButton(
            text="VSync",
            pos=(-0.3, 0, y_pos),
            scale=0.09,
            indicatorValue=self.settings.get('vsync', True),
            command=self._on_vsync_toggle,
            extraArgs=['vsync']
        )
        self.check_buttons['vsync'].reparentTo(self.frame)  # Parent to frame instead

        # Back button
        self.add_button(
            "Back",
            self._on_settings_back,
            pos=(0, 0, -0.4),
            scale=0.12
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
        current_value = self.check_buttons[setting_name]['indicatorValue']
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
        current_value = self.check_buttons[setting_name]['indicatorValue']
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
            self.settings[key] = checkbox['indicatorValue']
            
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

        # Settings menu created later to avoid conflicts
        # self.settings_menu = SettingsMenu(
        #     self.app,
        #     callbacks.get('back_to_main', lambda: None),
        #     callbacks.get('settings_data', {})
        # )

    def show_menu(self, menu_type: str):
        """Show a specific menu and hide others - with proper cleanup."""
        
        # First, completely hide all menus to prevent overlap
        self.hide_menus()

        # Show requested menu
        if menu_type == 'main':
            if self.main_menu:
                self.current_menu = self.main_menu
        elif menu_type == 'pause':
            if self.pause_menu:
                self.current_menu = self.pause_menu
        elif menu_type == 'game_over':
            if self.game_over_menu:
                self.current_menu = self.game_over_menu
        elif menu_type == 'settings':
            # Create settings menu if not already created
            if self.settings_menu is None:
                self.settings_menu = SettingsMenu(
                    self.app,
                    self.callbacks.get('back_to_main', lambda: None),
                    self.callbacks.get('settings_data', {})
                )
            self.current_menu = self.settings_menu
        else:
            print(f"Invalid menu type: {menu_type}")
            return

        # Show the new menu
        if self.current_menu:
            self.current_menu.show()
            print(f"Showing {menu_type} menu")
        else:
            print(f"Warning: {menu_type} menu not available")

    def hide_menus(self):
        """Hide all menus."""
        # Hide current menu and reset
        if self.current_menu:
            self.current_menu.hide()
        self.current_menu = None
        
        # Also hide individual menus to ensure cleanup
        menus = [self.main_menu, self.pause_menu, self.game_over_menu, self.settings_menu]
        for menu in menus:
            if menu and menu.visible:
                menu.hide()
        print("All menus hidden")

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