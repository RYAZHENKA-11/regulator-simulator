"""SDL2 window lifecycle and property management."""

import pathlib

try:
    import pygame
    from pygame._sdl2 import Renderer, Window
except ImportError as exc:
    raise ImportError(
        "pygame-ce is required, not classic pygame.\n"
        "Install it with: pip install pygame-ce."
    ) from exc

BASE_DIR = pathlib.Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
ICON_PATH = IMAGES_DIR / "robot.png"


class WindowManager:
    """Manages the SDL2 window lifecycle and properties.

    Attributes:
        size: Window dimensions ``(width, height)`` in pixels.
        width: Window width in pixels.
        height: Window height in pixels.
        position: Window position ``(x, y)`` in pixels.
    """

    _window: Window
    _initial_position: int | tuple[int, int]

    def __init__(
        self,
        size: tuple[int, int] = (640, 480),
        position: int | tuple[int, int] = pygame.WINDOWPOS_UNDEFINED,
        title: str = "Regulator simulator",
        fullscreen: bool = False,
        borderless: bool = False,
        resizable: bool = True,
        icon_path: pathlib.Path | str = ICON_PATH,
    ) -> None:
        """Initialize the window manager.

        The window is created hidden. Call ``show()`` to make it visible.

        Args:
            size: Initial window dimensions ``(width, height)`` in pixels.
                Defaults to ``(640, 480)``.
            position: Initial window position ``(x, y)`` in pixels or an SDL2
                position constant. Defaults to ``pygame.WINDOWPOS_UNDEFINED``.
            title: The window title. Defaults to ``"Regulator simulator"``.
            fullscreen: Whether the window should start in fullscreen mode.
                Defaults to ``False``.
            borderless: Whether the window should be borderless.
                Defaults to ``False``.
            resizable: Whether the window should be resizable.
                Defaults to ``True``.
            icon_path: Path to the window icon image. Defaults to ``ICON_PATH``.

        Raises:
            FileNotFoundError: If ``icon_path`` does not point to an existing file.
        """
        self._initial_position = position

        pygame.init()

        self._window = Window(
            title,
            size,
            self._initial_position,
            fullscreen=fullscreen,
            hidden=True,
            borderless=borderless,
            resizable=resizable,
        )
        try:
            self._window.set_icon(pygame.image.load(icon_path))
        except FileNotFoundError as exc:
            self._window.destroy()
            raise FileNotFoundError(f"Icon file not found: {icon_path}.") from exc

    @property
    def size(self) -> tuple[int, int]:
        """Window dimensions ``(width, height)`` in pixels."""
        return self._window.size

    @size.setter
    def size(self, size: tuple[int, int]) -> None:
        """Set the window dimensions ``(width, height)`` in pixels."""
        self._window.size = size

    @property
    def width(self) -> int:
        """Window width in pixels."""
        return self.size[0]

    @width.setter
    def width(self, width: int) -> None:
        """Set the window width in pixels."""
        self.size = (width, self.height)

    @property
    def height(self) -> int:
        """Window height in pixels."""
        return self.size[1]

    @height.setter
    def height(self, height: int) -> None:
        """Set the window height in pixels."""
        self.size = (self.width, height)

    @property
    def position(self) -> tuple[int, int]:
        """Window position ``(x, y)`` in pixels."""
        return self._window.position

    @position.setter
    def position(self, position: int | tuple[int, int]) -> None:
        """Set the window position ``(x, y)`` in pixels or an SDL2 position constant."""
        self._window.position = position

    def reset_position(self) -> None:
        """Reset the window position to its initial value."""
        self.position = self._initial_position

    def show(self) -> None:
        """Show the window."""
        self._window.show()

    def hide(self) -> None:
        """Hide the window."""
        self._window.hide()

    def destroy(self) -> None:
        """Destroy the window."""
        self._window.destroy()

    def create_renderer(self, vsync: bool = False) -> Renderer:
        """Create a renderer for the window.

        Args:
            vsync: Whether to enable vertical synchronization for the renderer.
                Defaults to ``False``.

        Returns:
            A new ``Renderer`` object associated with the window.
        """
        return Renderer(self._window, vsync=vsync)
