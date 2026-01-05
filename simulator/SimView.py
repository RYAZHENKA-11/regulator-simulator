import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Tuple, Optional

try:
    import pygame
    from pygame._sdl2 import Window, Renderer, Texture
except ModuleNotFoundError:
    print("Error: pygame-ce not found. Please install it via 'pip install pygame-ce'")
    sys.exit(1)

from . import Sim

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
ROBOT_IMG_PATH = IMAGES_DIR / "robot.png"
FORCE_IMG_PATH = IMAGES_DIR / "force.png"
WINDOW_ICON_PATH = IMAGES_DIR / "robot.png"

WINDOW_NAME = "Regulator simulator"
BACKGROUND_COLOR = (30, 33, 39, 255)
SURFACE_COLOR = (45, 50, 58, 255)
MARKER_COLOR = (0, 255, 200, 255)
STATIC_TEXT_COLOR = (160, 170, 185, 255)
DYNAMIC_TEXT_COLOR = (255, 215, 0, 255)

TEXT_OFFSET = 10
TEXT_STRING_INTERVAL = 1.2
FORCE_ROBOT_OFFSET = 250  # 180
SURFACE_ROBOT_OFFSET = 249
MARKER_WIDTH = 5
ROBOT_IMG_SIZE = 0.25

G = 9.8


@dataclass
class Settings:
    """Container for application settings."""

    wind_size: Optional[Tuple[int, int]] = None
    wind_position: Tuple[int, int] = (0, 0)
    scale: float = 1.0
    speed: float = 1.0

    def save(self, filename: str = ".settings.json") -> None:
        """
        Save current settings to JSON file.

        Args:
            filename: Path to the settings file
        """
        with open(filename, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def load(self, filename: str = ".settings.json") -> None:
        """
        Load settings from JSON file.

        Args:
            filename: Path to the settings file
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            for key, value in data.items():
                setattr(self, key, value)
        except FileNotFoundError:
            pass


class SimView:
    """
    Visualizer for the Sim system using pygame-ce.
    Handles rendering, user input, and video export.
    """

    def __init__(self,
                 simulator: Sim,
                 font_size: int = 20,
                 force_scale: float = 0.8,
                 ssaa: int = 2,
                 scale_quality: int = 2,
                 settings_filename: str = ".settings.json",
                 loading_settings: bool = True,
                 wind_size: Optional[Tuple[int, int]] = None,
                 speed: Optional[float] = None,
                 scale: Optional[float] = None):
        """
        Initialize the simulation visualizer.

        Args:
            simulator: The Sim instance to visualize
            force_scale: Visual multiplier for the force vector
            ssaa: Super-sampling anti-aliasing factor (e.g., 1, 2, 4)
            scale_quality: SDL2 scaling quality hint (0, 1, or 2):
                0: nearest pixel sampling
                1: linear filtering
                2: anisotropic filtering
            settings_filename: Path for saving/loading configuration
            loading_settings: Whether to load settings on startup
            wind_size: Initial window dimensions (width, height)
            speed: Simulation time multiplier
            scale: Visual zoom level
        """
        if scale_quality not in (0, 1, 2):
            raise ValueError("Scale quality must be 0, 1 or 2")

        self._settings = Settings()
        self._renderer: Optional[Renderer] = None
        self._running: Optional[bool] = None
        self._target_tex: Optional[Texture] = None
        self._draw_width: Optional[int] = None
        self._draw_height: Optional[int] = None
        self._draw_scale: Optional[float] = None
        self.pause: Optional[bool] = None
        self._center_x: Optional[float] = None
        self._center_y: Optional[float] = None
        self._angle: Optional[float] = None
        self._robot_tex: Optional[Texture] = None
        self._force_tex: Optional[Texture] = None
        self._font: Optional[pygame.font.Font] = None

        self.sim = simulator
        self._font_size = font_size
        self.force_scale = force_scale
        self._scale_quality = scale_quality
        self.settings_filename = settings_filename
        if loading_settings:
            self._settings.load(settings_filename)

        os.environ['SDL_RENDER_SCALE_QUALITY'] = str(self.scale_quality)
        pygame.init()
        pygame.font.init()

        self._window = Window(WINDOW_NAME, hidden=True)
        self._window.set_icon(pygame.image.load(WINDOW_ICON_PATH))
        self.ssaa = ssaa
        if wind_size is not None:
            self.wind_size = wind_size
        elif self._settings.wind_size is not None:
            self.wind_size = self._settings.wind_size
        else:
            size = pygame.display.get_desktop_sizes()[0]
            self.wind_size = (size[0] // 2, size[1] // 2)

        if speed is not None:
            self.speed = speed
        if scale is not None:
            self.scale = scale

    @property
    def force_scale(self) -> float:
        """Getter: returns the force scale value."""
        return self._force_scale

    @force_scale.setter
    def force_scale(self, force_scale: float) -> None:
        """Setter: adds validation logic."""
        if force_scale <= 0:
            raise ValueError("Force scale must be positive")
        self._force_scale = force_scale

    @property
    def font_size(self) -> int:
        """Getter: returns the font size value."""
        return self._font_size

    @font_size.setter
    def font_size(self, font_size: int) -> None:
        """Setter: adds validation logic."""
        if font_size <= 0:
            raise ValueError("Font size must be positive")
        self._font_size = font_size
        self._init_font()

    @property
    def ssaa(self) -> int:
        """Getter: returns the SSAA value."""
        return self._ssaa

    @ssaa.setter
    def ssaa(self, ssaa: int) -> None:
        """Setter: adds validation logic."""
        if math.log(ssaa, 2) % 1 != 0:
            raise ValueError("SSAA must be power of two. Usually 1/2/4")
        self._ssaa = ssaa
        self._draw_scale = self.scale * ssaa
        self._init_font()
        self._recreate_target_tex()

    @property
    def scale_quality(self) -> int:
        """Getter: returns the scale quality value."""
        return self._scale_quality

    @property
    def speed(self) -> float:
        """Getter: returns the speed value."""
        return self._settings.speed

    @speed.setter
    def speed(self, speed: float) -> None:
        """Setter: adds validation logic."""
        if speed <= 0:
            raise ValueError("Speed must be positive")
        self._settings.speed = speed

    @property
    def scale(self) -> float:
        """Getter: returns the speed value."""
        return self._settings.scale

    @scale.setter
    def scale(self, scale: float) -> None:
        """Setter: adds validation logic."""
        if scale <= 0:
            raise ValueError("Scale must be positive")
        self._settings.scale = scale
        self._draw_scale = self.scale * self.ssaa

    @property
    def wind_size(self) -> Tuple[int, int]:
        """Getter: returns the wind size value."""
        return self._window.size

    @wind_size.setter
    def wind_size(self, wind_size: Tuple[int, int]) -> None:
        """Setter: adds validation logic."""
        self._window.size = wind_size
        self._recreate_target_tex()

    @property
    def wind_position(self) -> Tuple[int, int]:
        """Getter: returns the wind size value."""
        return self._window.position

    @wind_position.setter
    def wind_position(self, wind_position: Tuple[int, int]) -> None:
        """Setter: adds validation logic."""
        self._window.position = wind_position

    def finish(self) -> None:
        """Finish simulation visualization."""
        self._running = False

    @property
    def is_running(self) -> bool:
        """Getter: returns whether the simulation has been started."""
        return self._running

    @property
    def is_pause(self) -> bool:
        """Getter: returns whether the simulation has been started."""
        return self.pause

    def _init_font(self):
        """Initialize the main render target texture."""
        self._font = pygame.font.SysFont(pygame.font.match_font('consolas', 'mono', 'monospace'),
                                         self.font_size * self.ssaa)

    def _recreate_target_tex(self):
        """Initialize the main render target texture."""
        if self._renderer is None:
            return
        self._draw_width = self.wind_size[0] * self.ssaa
        self._draw_height = self.wind_size[1] * self.ssaa
        self._center_x = self._draw_width * 0.5
        self._center_y = self._draw_height * 0.5
        if self._target_tex:
            del self._target_tex
        self._target_tex = Texture(self._renderer, (self._draw_width, self._draw_height), target=True)

    def _init_tex(self) -> None:
        """Loads image assets and creates SDL textures."""
        try:
            self._robot_tex = Texture.from_surface(self._renderer, pygame.image.load(ROBOT_IMG_PATH))
        except FileNotFoundError:
            raise FileNotFoundError("Robot image file not found")
        try:
            self._force_tex = Texture.from_surface(self._renderer, pygame.image.load(FORCE_IMG_PATH))
        except FileNotFoundError:
            raise FileNotFoundError("Force image file not found")

    def _process_events(self):
        """Handles window events and keyboard shortcuts (Reset, Pause, Quit)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.finish()
            if event.type == pygame.WINDOWCLOSE:
                self.finish()
            elif event.type == pygame.WINDOWRESIZED:
                self._recreate_target_tex()
            elif event.type == pygame.KEYDOWN:
                mode = pygame.key.get_mods()
                if event.scancode == pygame.KSCAN_R and not (mode & pygame.KMOD_SHIFT):
                    self.sim.reset()
                elif event.scancode == pygame.KSCAN_SPACE:
                    self.pause = not self.pause
                elif event.scancode == pygame.KSCAN_Q or (
                        event.scancode == pygame.KSCAN_W and mode & pygame.KMOD_CTRL):
                    self.finish()

    def _process_adjustment_keys(self, dt: float):
        """
        Handles continuous input for scale and speed adjustments.

        Args:
            dt: Delta time for smooth transitions
        """
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            if keys[pygame.K_EQUALS] or keys[pygame.K_KP_PLUS]:
                self.scale *= 1.0 + 2.0 * dt
            if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
                self.scale *= 1.0 - 2.0 * dt
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if keys[pygame.K_EQUALS] or keys[pygame.K_KP_PLUS]:
                self.speed *= 1.0 + 2.0 * dt
            if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
                self.speed *= 1.0 - 2.0 * dt
            if keys[pygame.K_r]:
                self.speed = 1.0

    def _draw_surface(self):
        """Renders the inclined surface based on external forces."""
        b = self._center_y + SURFACE_ROBOT_OFFSET * self._draw_scale / math.cos(math.radians(self._angle))
        k = math.tan(math.radians(self._angle))
        p1_y = max(0.0, min(k * -self._center_x + b, self._draw_height))
        p1_x = 0.0 if k == 0.0 else (p1_y - b) / k + self._center_x
        p2_y = max(0.0, min(k * self._center_x + b, self._draw_height))
        p2_x = self._draw_width if k == 0.0 else (p2_y - b) / k + self._center_x
        p3_x = min(self._draw_width, p2_x)
        p4_x = max(0.0, p1_x)
        self._renderer.draw_color = SURFACE_COLOR
        self._renderer.fill_quad((p1_x, p1_y),
                                 (p2_x, p2_y),
                                 (p3_x, self._draw_height),
                                 (p4_x, self._draw_height))
        self._renderer.fill_rect((0, p1_y, p1_x, self._draw_height - p1_y))
        self._renderer.fill_rect((p2_x, p2_y, self._draw_width - p2_x, self._draw_height - p2_y))

    def _draw_target_marker(self):
        """Renders the vertical marker at the target position."""
        self._renderer.draw_color = MARKER_COLOR
        b = self._center_y
        k = math.tan(math.radians(self._angle + 90.0))
        x = (self.sim.target_x * self._robot_tex.width * self._draw_scale / ROBOT_IMG_SIZE / math.cos(
            math.radians(self._angle))
             + self._center_x)
        p1_x = (0.0 - b) / k + x
        p2_x = (self._draw_height - b) / k + x
        self._renderer.fill_quad(
            (p1_x - max(MARKER_WIDTH * self._draw_scale, self.ssaa * 0.5) / math.cos(math.radians(self._angle)), 0.0),
            (p1_x + max(MARKER_WIDTH * self._draw_scale, self.ssaa * 0.5) / math.cos(math.radians(self._angle)), 0.0),
            (p2_x + max(MARKER_WIDTH * self._draw_scale, self.ssaa * 0.5) / math.cos(math.radians(self._angle)),
             self._draw_height),
            (p2_x - max(MARKER_WIDTH * self._draw_scale, self.ssaa * 0.5) / math.cos(math.radians(self._angle)),
             self._draw_height))

    def _draw_robot_with_forces(self):
        """Renders the robot sprite and the force vector arrow."""
        x = (self.sim.x * math.cos(
            math.radians(self._angle)) * self._robot_tex.width * self._draw_scale / ROBOT_IMG_SIZE
             + self._center_x)
        y = (self.sim.x * math.sin(
            math.radians(self._angle)) * self._robot_tex.width * self._draw_scale / ROBOT_IMG_SIZE
             + self._center_y)

        force_width = self._force_tex.width * self._draw_scale * self.force_scale * math.log(abs(self.sim.f) + 1)
        force_height = self._force_tex.height * self._draw_scale
        if self.sim.f < 0:
            self._force_tex.draw(dstrect=(x - FORCE_ROBOT_OFFSET * self._draw_scale - force_width,
                                          y - force_height * 0.5,
                                          force_width, force_height),
                                 angle=self._angle,
                                 origin=(round(force_width + FORCE_ROBOT_OFFSET * self._draw_scale),
                                         round(force_height * 0.5)),
                                 flip_x=False)
        else:
            self._force_tex.draw(dstrect=(x + FORCE_ROBOT_OFFSET * self._draw_scale, y - force_height * 0.5,
                                          force_width, force_height),
                                 angle=self._angle,
                                 origin=(round(-FORCE_ROBOT_OFFSET * self._draw_scale), round(force_height * 0.5)),
                                 flip_x=True)

        robot_width = self._robot_tex.width * self._draw_scale
        robot_height = self._robot_tex.height * self._draw_scale
        self._robot_tex.draw(dstrect=(x - robot_width * 0.5, y - robot_height * 0.5,
                                      robot_width, robot_height),
                             angle=self._angle)

    def _draw_system_state(self):
        """Renders system status information."""
        static_system_status = [
            f"M: {self.sim.m:.1f} kg",
            f"Damping: {self.sim.damping:.1f} N·s/m",
            f"External F: {self.sim.external_f:.1f} N",
            f"Freq: {self.sim.freq:.1f} Hz",
            f"Target: {self.sim.target_x:.1f} m",
            f"X0: {self.sim.x0:.1f} m",
            f"V0: {self.sim.v0:.1f} m/s",
            f"F0: {self.sim.f0:.1f} N",
        ]
        dynamic_system_status = [
            f"X: {self.sim.x:.3f} m",
            f"V: {self.sim.v:.3f} m/s",
            f"F: {self.sim.f:.3f} N",
        ]
        static_control_keys = [
            "Scale: Ctrl +/-",
            "Speed: Shift +/-",
            "Speed=1: Shift+R",
            "Restart: R",
            "Pause: Space",
            "Exit: Q / Ctrl+W",
        ]
        static_view_status = [
            f"Scale: {self.scale:.2f}",
            f"Speed: {self.speed:.2f}",
            "PAUSED" if self.is_pause else "RUNNING",
        ]
        x_offset = TEXT_OFFSET * self.ssaa
        y_offset = TEXT_OFFSET * self.ssaa

        for i, line in enumerate(static_system_status[::-1]):
            text_surf = self._font.render(line, True, STATIC_TEXT_COLOR)
            text_tex = Texture.from_surface(self._renderer, text_surf)
            w, h = text_surf.get_size()
            text_tex.draw(dstrect=(x_offset, self._draw_height - y_offset - (i + 1) * h * TEXT_STRING_INTERVAL))
        for i, line in enumerate(dynamic_system_status):
            text_surf = self._font.render(line, True, DYNAMIC_TEXT_COLOR)
            text_tex = Texture.from_surface(self._renderer, text_surf)
            w, h = text_tex.width, text_tex.height
            text_tex.draw(dstrect=(x_offset, y_offset + i * h * TEXT_STRING_INTERVAL))
        for i, line in enumerate(static_control_keys):
            text_surf = self._font.render(line, True, STATIC_TEXT_COLOR)
            text_tex = Texture.from_surface(self._renderer, text_surf)
            w, h = text_surf.get_size()
            text_tex.draw(dstrect=(self._draw_width - x_offset - w, y_offset + i * h * TEXT_STRING_INTERVAL))
        for i, line in enumerate(static_view_status):
            text_surf = self._font.render(line, True, STATIC_TEXT_COLOR)
            text_tex = Texture.from_surface(self._renderer, text_surf)
            w, h = text_surf.get_size()
            text_tex.draw(dstrect=(self._draw_width - x_offset - w,
                                   self._draw_height - y_offset - (i + 1) * h * TEXT_STRING_INTERVAL))

    def _init_renderer(self, vsync: bool = False):
        """
        Initializes the SDL2 Renderer and prepares assets.

        Args:
            vsync: Whether to enable vertical synchronization
        """
        if self._renderer is not None:
            self._target_tex = None
            self._robot_tex = None
            self._force_tex = None
            del self._renderer
            self._renderer = None
        self._renderer = Renderer(self._window, vsync=vsync)
        self._init_tex()
        self._recreate_target_tex()

    def _render(self):
        """Main rendering pipeline: calculates angle and draws all components to target texture."""
        self._angle = math.degrees(math.asin(max(-1.0, min(self.sim.external_f / (self.sim.m * G), 1.0))))

        self._renderer.target = self._target_tex
        self._renderer.draw_color = BACKGROUND_COLOR
        self._renderer.clear()

        self._draw_surface()
        self._draw_target_marker()
        self._draw_robot_with_forces()
        self._draw_system_state()

    def run(self,
            fps: int = 0,
            vsync: bool = True,
            borderless: bool = False,
            fullscreen: bool = False,
            wind_position: Optional[Tuple[int, int]] = None,
            saving_settings: bool = True):
        """
        Starts the interactive simulation loop.

        Args:
            fps: Maximum frames per second (0 for uncapped)
            vsync: Enable vertical sync
            borderless: Run in borderless window mode
            fullscreen: Run in fullscreen mode
            wind_position: Initial window position
            saving_settings: Whether to save settings to disk on exit
        """
        if fps < 0:
            raise ValueError("FPS cannot be negative")
        if fps == 0 and not vsync:
            raise ValueError("You should set fps != 0 while vsync is False")
        if wind_position is not None:
            self._settings.wind_position = wind_position

        self._window.resizable = True
        self._window.borderless = borderless
        if fullscreen:
            self._window.set_fullscreen(True)
        self._window.show()
        self._init_renderer(vsync)

        self.pause = False
        first_frame = True
        self._running = True
        clock = pygame.time.Clock()
        try:
            while self.is_running:
                self._process_events()
                dt = min(clock.tick(fps) / 1000.0, 0.1)
                self._process_adjustment_keys(dt)

                if not self.is_pause:
                    self.sim.simulate_dt(dt * self.speed)

                self._render()
                self._renderer.target = None
                self._target_tex.draw(dstrect=(0.0, 0.0, self.wind_size[0], self.wind_size[1]))
                self._renderer.present()

                if first_frame:
                    first_frame = False
                    if wind_position is None:
                        self.wind_position = self._settings.wind_position
            if saving_settings:
                self._settings.wind_position = self.wind_position
                self._settings.wind_size = self.wind_size
                self._settings.save(self.settings_filename)
        finally:
            self._window.hide()

    def save_video(self,
                   seconds: float = 5.0,
                   filename: str = "simulation.mp4",
                   fps: int = 60,
                   quality: int = 0):
        """
        Records the simulation to a video file using FFmpeg.

        Args:
            seconds: Duration of the video in simulation seconds
            filename: Output file path
            fps: Video frame rate
            quality: H.264 CRF value (0-51, lower is better)
        """
        if fps < 0:
            raise ValueError("FPS cannot be negative")
        if quality < 0 or quality > 51:
            raise ValueError("Quality must be between 0 and 51")
        if shutil.which('ffmpeg') is None:
            print("Error: ffmpeg not found in PATH")
            return

        wind_size = list(self.wind_size)
        if wind_size[0] % 2 == 1:
            wind_size[0] += 1
        if wind_size[1] % 2 == 1:
            wind_size[1] += 1
        self.wind_size = wind_size
        self._init_renderer()

        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{self.wind_size[0]}x{self.wind_size[1]}',
            '-pix_fmt', 'bgra',
            '-r', str(fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', str(quality),
            '-pix_fmt', 'yuv420p',
            filename
        ]

        dt = (1.0 / fps) * self.speed
        time = 0
        capture_texture = Texture(self._renderer, self.wind_size, target=True)
        capture_surface = pygame.Surface(self.wind_size, pygame.SRCALPHA)
        with subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE) as ffmpeg_proc:
            while time < seconds:
                time += dt
                self.sim.simulate_dt(dt)
                self._render()
                self._renderer.target = capture_texture
                self._target_tex.draw(dstrect=(0.0, 0.0, self.wind_size[0], self.wind_size[1]))
                self._renderer.to_surface(surface=capture_surface)
                pixels = capture_surface.get_view().raw
                try:
                    ffmpeg_proc.stdin.write(pixels)
                except BrokenPipeError:
                    print("FFmpeg process crashed.")
                    break
