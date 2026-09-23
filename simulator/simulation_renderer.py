"""Rendering of the simulation state to a ``GraphicsRenderer``."""

import math
import pathlib

try:
    import pygame
    from pygame._sdl2 import Texture
except ImportError as exc:
    raise ImportError(
        "pygame-ce is required, not classic pygame.\n"
        "Install it with: pip install pygame-ce."
    ) from exc

from .graphics_renderer import GraphicsRenderer
from .simulator import Simulator

BASE_DIR = pathlib.Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
FONTS_DIR = BASE_DIR / "fonts"
ROBOT_IMG_PATH = IMAGES_DIR / "robot.png"
FORCE_IMG_PATH = IMAGES_DIR / "arrow.png"
FONT_PATH = FONTS_DIR / "Inter-Medium.ttf"

MAX_ANGLE_SIN: float = 0.99999
SURFACE_OFFSET_PX: float = 249.0
FORCE_OFFSET_PX: float = 250.0
MARKER_WIDTH_PX: float = 5.0
FONT_OFFSET_PX: float = 10.0
TEXT_LINE_SPACING: float = 1.2

Color = tuple[int, int, int] | tuple[int, int, int, int]
BACKGROUND_COLOR: Color = (30, 33, 39)
SURFACE_COLOR: Color = (45, 50, 58)
MARKER_COLOR: Color = (0, 255, 200)
STATIC_TEXT_COLOR: Color = (160, 170, 185)
DYNAMIC_TEXT_COLOR: Color = (255, 215, 0)

GRAVITY_ACCELERATION: float = 9.8
ROBOT_SIZE_M: float = 0.25


class SimulationRenderer:
    """Handles the rendering of the simulation state.

    Attributes:
        scale: Visual zoom level.
        arrow_scale: Visual multiplier for the force vector.
        width: Width of the graphics renderer. Read-only.
        height: Height of the graphics renderer. Read-only.
        center_x: Horizontal center of the render target in logical pixels. Read-only.
        center_y: Vertical center of the render target in logical pixels. Read-only.
        angle: Current angle of the inclined surface in radians. Read-only.
    """

    _simulator: Simulator
    _graphics_renderer: GraphicsRenderer
    _scale: float
    _arrow_scale: float
    _font_size: int
    _robot_tex: Texture
    _arrow_tex: Texture
    _font: pygame.font.Font

    def __init__(
        self,
        simulator: Simulator,
        graphics_renderer: GraphicsRenderer,
        scale: float = 0.1,
        arrow_scale: float = 1.0,
        font_size: int = 20,
    ) -> None:
        """Initialize the simulation renderer.

        Args:
            simulator: The ``Simulator`` instance containing the simulation state.
            graphics_renderer: The ``GraphicsRenderer`` instance for rendering.
            scale: Visual zoom level. Must be positive. Defaults to ``0.1``.
            arrow_scale: Visual multiplier for the force vector. Must be positive.
                Defaults to ``1.0``.
            font_size: Size of the font on screen. Must be a positive integer.
                Defaults to ``20``.

        Raises:
            ValueError: If ``scale`` or ``arrow_scale`` is not positive or
                if ``font_size`` is not a positive integer.
        """
        if (
            not isinstance(font_size, int)
            or isinstance(font_size, bool)
            or font_size <= 0
        ):
            raise ValueError("Font size must be a positive integer.")

        self._simulator = simulator
        self._graphics_renderer = graphics_renderer
        self.scale = scale
        self.arrow_scale = arrow_scale
        self._font_size = font_size

        pygame.init()

        self._robot_tex = self._graphics_renderer.create_texture(ROBOT_IMG_PATH)
        self._arrow_tex = self._graphics_renderer.create_texture(FORCE_IMG_PATH)
        self._font = self._graphics_renderer.create_font(FONT_PATH, self._font_size)

    @property
    def scale(self) -> float:
        """Visual zoom level."""
        return self._scale

    @scale.setter
    def scale(self, scale: float) -> None:
        """Set visual zoom level. Must be positive.

        Raises:
            ValueError: If ``scale`` is not positive.
        """
        if scale <= 0.0:
            raise ValueError("Scale must be positive.")
        self._scale = scale

    @property
    def arrow_scale(self) -> float:
        """Visual multiplier for the force vector."""
        return self._arrow_scale

    @arrow_scale.setter
    def arrow_scale(self, arrow_scale: float) -> None:
        """Set the visual multiplier for the force vector. Must be positive.

        Raises:
            ValueError: If ``arrow_scale`` is not positive.
        """
        if arrow_scale <= 0.0:
            raise ValueError("Arrow scale must be positive.")
        self._arrow_scale = arrow_scale

    @property
    def width(self) -> int:
        """Width of the graphics renderer."""
        return self._graphics_renderer.width

    @property
    def height(self) -> int:
        """Height of the graphics renderer."""
        return self._graphics_renderer.height

    @property
    def center_x(self) -> float:
        """Horizontal center of the render target in logical pixels."""
        return self._graphics_renderer.width * 0.5

    @property
    def center_y(self) -> float:
        """Vertical center of the render target in logical pixels."""
        return self._graphics_renderer.height * 0.5

    @property
    def angle(self) -> float:
        """Current angle of the inclined surface in radians."""
        value = self._simulator.external_f / (self._simulator.m * GRAVITY_ACCELERATION)
        return math.asin(max(-MAX_ANGLE_SIN, min(value, MAX_ANGLE_SIN)))

    def _draw_background(self) -> None:
        """Draw the background color."""
        self._graphics_renderer.set_color(BACKGROUND_COLOR)
        self._graphics_renderer.clear()

    def _draw_surface(self) -> None:
        """Draw the surface based on the current angle."""
        y_at_center = self.center_y + SURFACE_OFFSET_PX * self.scale / math.cos(
            self.angle
        )
        slope = math.tan(self.angle)
        left_y = max(0.0, min(-slope * self.center_x + y_at_center, self.height))
        right_y = max(0.0, min(slope * self.center_x + y_at_center, self.height))
        if math.isclose(slope, 0.0):
            left_x = 0.0
            right_x = self.width
        else:
            left_x = (left_y - y_at_center) / slope + self.center_x
            right_x = (right_y - y_at_center) / slope + self.center_x

        self._graphics_renderer.set_color(SURFACE_COLOR)
        self._graphics_renderer.fill_quad(
            (left_x, left_y),
            (right_x, right_y),
            (right_x, self.height),
            (left_x, self.height),
        )
        self._graphics_renderer.fill_rect((0.0, left_y, left_x, self.height - left_y))
        self._graphics_renderer.fill_rect(
            (right_x, right_y, self.width - right_x, self.height - right_y)
        )

    def _draw_target_marker(self) -> None:
        """Draw a marker line at the target position."""
        offset = (
            self._simulator.target_x * self._robot_tex.width * self.scale / ROBOT_SIZE_M
        )
        x = offset / math.cos(self.angle) + self.center_x
        half_w = max(MARKER_WIDTH_PX * self.scale, 0.5) / math.cos(self.angle)
        if math.isclose(math.tan(self.angle), 0.0):
            up_x = x
            down_x = x
        else:
            slope = -1.0 / math.tan(self.angle)
            up_x = (0.0 - self.center_y) / slope + x
            down_x = (self.height - self.center_y) / slope + x

        self._graphics_renderer.set_color(MARKER_COLOR)
        self._graphics_renderer.fill_quad(
            (up_x - half_w, 0.0),
            (up_x + half_w, 0.0),
            (down_x + half_w, self.height),
            (down_x - half_w, self.height),
        )

    def _draw_robot_with_arrows(self) -> None:
        """Draw the robot and the force arrows."""
        offset = self._simulator.x * self._robot_tex.width * self.scale / ROBOT_SIZE_M
        x = offset * math.cos(self.angle) + self.center_x
        y = offset * math.sin(self.angle) + self.center_y

        robot_w = self._robot_tex.width * self.scale
        robot_h = self._robot_tex.height * self.scale
        self._graphics_renderer.draw_texture(
            self._robot_tex,
            dstrect=(x - robot_w * 0.5, y - robot_h * 0.5, robot_w, robot_h),
            angle=math.degrees(self.angle),
        )

        arrow_size = self.arrow_scale * math.log(abs(self._simulator.f) + 1.0)
        arrow_w = self._arrow_tex.width * self.scale * arrow_size
        arrow_h = self._arrow_tex.height * self.scale
        if not math.isclose(self._simulator.f, 0.0):
            if self._simulator.f < 0.0:
                arrow_x = x - FORCE_OFFSET_PX * self.scale - arrow_w
                origin_x = arrow_w + FORCE_OFFSET_PX * self.scale
                flip_x = False
            else:
                arrow_x = x + FORCE_OFFSET_PX * self.scale
                origin_x = -FORCE_OFFSET_PX * self.scale
                flip_x = True
            self._graphics_renderer.draw_texture(
                self._arrow_tex,
                dstrect=(arrow_x, y - arrow_h * 0.5, arrow_w, arrow_h),
                angle=math.degrees(self.angle),
                origin=(origin_x, arrow_h * 0.5),
                flip_x=flip_x,
            )

    def _draw_system_state(self, view_status_text: tuple[str, ...]) -> None:
        """Draw system state information.

        Args:
            view_status_text: Lines of the view status text to draw
                in the bottom-right corner.
        """
        self._graphics_renderer.draw_text(
            (
                f"X: {self._simulator.x:.3f} m",
                f"V: {self._simulator.v:.3f} m/s",
                f"F: {self._simulator.f:.3f} N",
            ),
            self._font,
            "up-left",
            DYNAMIC_TEXT_COLOR,
            FONT_OFFSET_PX,
            TEXT_LINE_SPACING,
        )
        self._graphics_renderer.draw_text(
            (
                f"M: {self._simulator.m:.1f} kg",
                f"Damping: {self._simulator.damping:.1f} N·s/m",
                f"External F: {self._simulator.external_f:.1f} N",
                f"Freq: {self._simulator.freq:.1f} Hz",
                f"Target: {self._simulator.target_x:.1f} m",
                f"X0: {self._simulator.x0:.1f} m",
                f"V0: {self._simulator.v0:.1f} m/s",
                f"F0: {self._simulator.f0:.1f} N",
            ),
            self._font,
            "down-left",
            STATIC_TEXT_COLOR,
            FONT_OFFSET_PX,
            TEXT_LINE_SPACING,
        )
        self._graphics_renderer.draw_text(
            (
                "Scale: Ctrl +/-",
                "Speed: Shift +/-",
                "Speed=1: Shift+R",
                "Restart: R",
                "Pause: Space",
                "Exit: Q / Ctrl+W",
            ),
            self._font,
            "up-right",
            STATIC_TEXT_COLOR,
            FONT_OFFSET_PX,
            TEXT_LINE_SPACING,
        )
        self._graphics_renderer.draw_text(
            view_status_text,
            self._font,
            "down-right",
            STATIC_TEXT_COLOR,
            FONT_OFFSET_PX,
            TEXT_LINE_SPACING,
        )

    def render(self, view_status_text: tuple[str, ...]) -> None:
        """Render the current simulation state.

        Args:
            view_status_text: Lines of the view status text to draw
                in the bottom-right corner.
        """
        self._draw_background()
        self._draw_surface()
        self._draw_target_marker()
        self._draw_robot_with_arrows()
        self._draw_system_state(view_status_text)
