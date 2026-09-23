"""Simulation video export via FFmpeg."""

import shutil
import subprocess

try:
    import pygame
except ImportError as exc:
    raise ImportError(
        "pygame-ce is required, not classic pygame.\n"
        "Install it with: pip install pygame-ce."
    ) from exc

from .graphics_renderer import GraphicsRenderer
from .simulation_renderer import SimulationRenderer
from .simulator import Simulator


class VideoExporter:
    """Coordinates the hidden-window simulation loop via FFmpeg."""

    _graphics_renderer: GraphicsRenderer
    _simulation_renderer: SimulationRenderer
    _simulator: Simulator

    def __init__(
        self,
        graphics_renderer: GraphicsRenderer,
        simulation_renderer: SimulationRenderer,
        simulator: Simulator,
    ) -> None:
        """Initialize the video exporter.

        Args:
            graphics_renderer: The ``GraphicsRenderer`` instance
                for managing the graphics rendering.
            simulation_renderer: The ``SimulationRenderer`` instance
                for managing the simulation rendering.
            simulator: The ``Simulator`` instance
                for managing the simulation.
        """
        self._graphics_renderer = graphics_renderer
        self._simulation_renderer = simulation_renderer
        self._simulator = simulator

    def export(
        self,
        seconds: float = 10.0,
        speed: float = 1.0,
        filename: str = "simulation.mp4",
        fps: int = 60,
        ffmpeg_options: tuple[str, ...] | None = None,
    ) -> None:
        """Record the simulation to a video file using FFmpeg.

        Args:
            seconds: Duration of the video in simulation seconds.
                Must be positive. Defaults to ``10.0``.
            speed: The simulation speed multiplier.
                Must be positive. Defaults to ``1.0``.
            filename: Output file path. Must be ``.mp4``.
                Defaults to ``"simulation.mp4"``.
            fps: Video frame rate. Must be a positive integer. Defaults to ``60``.
            ffmpeg_options: Extra command-line arguments for FFmpeg
                like ``('-crf', '23')``. Defaults to ``None``.

        Raises:
            FileNotFoundError: If ffmpeg not found in PATH.
            ValueError: If ``speed`` is not positive,
                ``seconds`` is not positive,
                ``filename`` is not a ``.mp4``, or
                ``fps`` is not a positive integer.
            RuntimeError: If FFmpeg failed to encode the video.
        """
        if shutil.which("ffmpeg") is None:
            raise FileNotFoundError("ffmpeg not found in PATH.")
        if speed <= 0:
            raise ValueError("Speed must be positive.")
        if seconds <= 0:
            raise ValueError("Seconds must be positive.")
        if not filename.endswith(".mp4"):
            raise ValueError("Filename must end with .mp4.")
        if not isinstance(fps, int) or isinstance(fps, bool) or fps <= 0:
            raise ValueError("Video frame rate must be a positive integer.")

        width = self._graphics_renderer.width + (self._graphics_renderer.width % 2)
        height = self._graphics_renderer.height + (self._graphics_renderer.height % 2)
        if (width, height) != self._graphics_renderer.size:
            print(f"Resolution={width}x{height} for compatibility with libx264.")
            self._graphics_renderer.size = (width, height)

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-s",
            f"{width}x{height}",
            "-pix_fmt",
            "bgra",
            "-r",
            f"{fps}",
            "-i",
            "-",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            *(ffmpeg_options or []),
            filename,
        ]

        dt = (1.0 / fps) * speed
        sim_time = 0.0
        capture_texture = self._graphics_renderer.create_texture(
            self._graphics_renderer.size, target=True
        )
        capture_surface = pygame.Surface(self._graphics_renderer.size, pygame.SRCALPHA)
        with subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE) as ffmpeg_proc:
            completed = True
            while sim_time < seconds and completed:
                sim_time += dt
                self._simulator.simulate_dt(dt)
                self._simulation_renderer.render((f"Speed: {speed:.2f}",))
                self._graphics_renderer.present(capture_texture, capture_surface)
                try:
                    ffmpeg_proc.stdin.write(capture_surface.get_view().raw)
                except BrokenPipeError:
                    completed = False
            try:
                ffmpeg_proc.stdin.close()
            except BrokenPipeError:
                pass
        if not completed or ffmpeg_proc.returncode != 0:
            raise RuntimeError(
                "FFmpeg failed to encode the video "
                f"(exit code {ffmpeg_proc.returncode})."
            )
