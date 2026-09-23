"""A complete, beginner-friendly example: a PID regulator in action.

This is the single ready-to-run example of the ``simulator`` package.
It wires up the full stack (window, graphics, physics and regulator) and
remembers your preferences between runs.

The easiest way to experiment: change the constants at the top of this
file (regulator coefficients, robot physics) and launch the simulation
again.
"""

import argparse
import sys

from simulator import (
    GraphicsRenderer,
    PlayerController,
    Settings,
    SimulationRenderer,
    Simulator,
    VideoExporter,
    WindowManager,
)

# Regulator coefficients.
P_COEF: float = 10.0  # P (proportional)
I_COEF: float = 5.0  # I (integral)
D_COEF: float = 5.0  # D (differential)
INTEGRAL_LIMIT: float = 0.5  # clamps the accumulated error

# Robot physics.
MASS: float = 1.0  # robot mass, kg
DAMPING: float = 1.0  # friction, N·s/m
EXTERNAL_FORCE: float = 1.0  # constant force pushing the robot, N
SAMPLING_FREQUENCY: float = 100.0  # how often the regulator runs, Hz
TARGET_POSITION: float = -1.0  # where the robot should stop, m
START_POSITION: float = 1.0  # where the robot starts, m
START_VELOCITY: float = 0.0  # starting velocity, m/s


class PIDRegulator:
    """PID regulator: converts the simulation state into a control force.

    ``__call__`` is the interface used by ``Simulator``: it receives the
    state and returns the control force.
    """

    def __init__(
        self, p_coef: float, i_coef: float, d_coef: float, integral_limit: float
    ) -> None:
        """Initialize the regulator.

        Args:
            p_coef: Proportional coefficient.
            i_coef: Integral coefficient.
            d_coef: Differential coefficient.
            integral_limit: Maximum absolute value of the accumulated integral.
        """
        self._p_coef = p_coef
        self._i_coef = i_coef
        self._d_coef = d_coef
        self._integral_limit = integral_limit
        self._integral = 0.0

    def __call__(
        self, x: float, target_x: float, v: float, step_integral: float
    ) -> float:
        """Compute the control force.

        Args:
            x: Current position in meters.
            target_x: Target position in meters.
            v: Current velocity in meters per second.
            step_integral: Integral of the position deviation accumulated
                since the last call, in meter-seconds (m·s).

        Returns:
            The control force in newtons.
        """
        deviation = x - target_x
        self._integral += step_integral
        self._integral = max(
            -self._integral_limit, min(self._integral, self._integral_limit)
        )
        return -(
            deviation * self._p_coef + self._integral * self._i_coef + v * self._d_coef
        )

    def reset(self) -> None:
        """Reset the internal state. Called by the simulator on restart."""
        self._integral = 0.0


def build_app(
    settings: Settings,
) -> tuple[WindowManager, GraphicsRenderer, SimulationRenderer, Simulator]:
    """Create the window, renderers and simulation from the settings.

    This is the "recipe" of the example: the simulator runs the physics,
    the window displays it, and the two renderers draw it (the graphics
    renderer knows *how* to draw, the simulation renderer knows *what*
    to draw).

    Returns:
        The window manager, graphics renderer, simulation renderer
        and simulator, in that order.
    """
    regulator = PIDRegulator(
        p_coef=P_COEF, i_coef=I_COEF, d_coef=D_COEF, integral_limit=INTEGRAL_LIMIT
    )
    simulator = Simulator(
        regulator,
        regulator.reset,
        m=MASS,
        damping=DAMPING,
        external_f=EXTERNAL_FORCE,
        freq=SAMPLING_FREQUENCY,
        target_x=TARGET_POSITION,
        x0=START_POSITION,
        v0=START_VELOCITY,
    )
    window_manager = WindowManager(
        size=settings.window_size,
        position=settings.window_position,
    )
    graphics_renderer = GraphicsRenderer(window_manager)
    simulation_renderer = SimulationRenderer(
        simulator, graphics_renderer, scale=settings.scale
    )
    return window_manager, graphics_renderer, simulation_renderer, simulator


def run_interactive(settings: Settings) -> None:
    """Open the interactive window and save the settings when it closes."""
    window_manager, graphics_renderer, simulation_renderer, simulator = build_app(
        settings
    )
    player_controller = PlayerController(
        window_manager,
        graphics_renderer,
        simulation_renderer,
        simulator,
        speed=settings.speed,
    )
    player_controller.run()

    settings.window_size = window_manager.size
    settings.window_position = window_manager.position
    settings.scale = simulation_renderer.scale
    settings.speed = player_controller.speed
    settings.save()


def run_export(
    settings: Settings, seconds: float, speed: float, filename: str, fps: int
) -> None:
    """Render a video to a mp4 file without showing a window.

    The video is rendered at the saved window size and zoom. Settings are
    not changed by the export.
    """
    _window_manager, graphics_renderer, simulation_renderer, simulator = build_app(
        settings
    )
    video_exporter = VideoExporter(graphics_renderer, simulation_renderer, simulator)
    video_exporter.export(seconds, speed, filename, fps)


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and run the selected mode.

    Args:
        argv: Command-line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code.
    """
    parser = argparse.ArgumentParser(description="Regulator simulator example")
    parser.add_argument(
        "--export",
        action="store_true",
        help="render a video to simulation.mp4 instead of opening a window",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=10.0,
        help="video duration in simulation seconds (with --export)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="simulation speed multiplier (with --export)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="simulation.mp4",
        help="output file mp4 name (with --export)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="video frame rate (with --export)",
    )
    args = parser.parse_args(argv)

    settings = Settings()
    settings.load()
    if args.export:
        run_export(settings, args.seconds, args.speed, args.name, args.fps)
    else:
        run_interactive(settings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
