"""Low-level SDL2 rendering with supersampling anti-aliasing."""

import math
import os
import pathlib

try:
    import pygame
    from pygame._sdl2 import Renderer, Texture
except ImportError as exc:
    raise ImportError(
        "pygame-ce is required, not classic pygame.\n"
        "Install it with: pip install pygame-ce."
    ) from exc

from .window_manager import WindowManager


class GraphicsRenderer:
    """Handles SDL2 low-level rendering with SSAA and scale quality.

    Attributes:
        size: Logical render size ``(width, height)`` in logical pixels.
        width: Logical render width in logical pixels.
        height: Logical render height in logical pixels.
    """

    _window_manager: WindowManager
    _ssaa: int
    _scale_quality: int
    _renderer: Renderer
    _size: tuple[int, int]
    _target_texture: Texture

    def __init__(
        self,
        window_manager: WindowManager,
        ssaa: int = 2,
        scale_quality: int = 2,
        vsync: bool = True,
    ) -> None:
        """Initialize the graphics renderer.

        Args:
            window_manager: The ``WindowManager`` instance whose SDL2 window
                will be rendered to.
            ssaa: Supersampling Anti-Aliasing factor. Must be a power of two.
                Usually ``1``/``2``/``4``/``8``. Defaults to ``2``.
            scale_quality: SDL2 scale quality:
                ``0`` for nearest pixel sampling,
                ``1`` for linear filtering,
                ``2`` for anisotropic filtering.
                Defaults to ``2``.
            vsync: Whether to enable vertical synchronization.
                Defaults to ``True``.

        Raises:
            ValueError: If ``ssaa`` is not a power of two or
                ``scale_quality`` is not ``0``/``1``/``2``.
        """
        if ssaa <= 0 or not math.isclose(math.log2(ssaa) % 1, 0.0):
            raise ValueError(
                "Supersampling Anti-Aliasing factor must be a power of two. "
                "Usually 1/2/4/8."
            )
        if scale_quality not in (0, 1, 2):
            raise ValueError("Scale quality must be 0/1/2.")

        self._window_manager = window_manager
        self._ssaa = ssaa
        self._scale_quality = scale_quality

        pygame.init()
        os.environ["SDL_RENDER_SCALE_QUALITY"] = str(self._scale_quality)

        self._renderer = window_manager.create_renderer(vsync)
        self._size, self._target_texture = self._recreate_target_texture()

    @property
    def size(self) -> tuple[int, int]:
        """Logical render size ``(width, height)`` in logical pixels."""
        return self._size

    @size.setter
    def size(self, size: tuple[int, int]) -> None:
        """Set the logical render size ``(width, height)`` in logical pixels."""
        self._window_manager.size = size
        self.update_target_texture()

    @property
    def width(self) -> int:
        """Logical render width in logical pixels."""
        return self.size[0]

    @width.setter
    def width(self, width: int) -> None:
        """Set the logical render width in logical pixels."""
        self.size = (width, self.height)

    @property
    def height(self) -> int:
        """Logical render height in logical pixels."""
        return self.size[1]

    @height.setter
    def height(self, height: int) -> None:
        """Set the logical render height in logical pixels."""
        self.size = (self.width, height)

    def _recreate_target_texture(self) -> tuple[tuple[int, int], Texture]:
        """Recreate the target texture from the current window size and SSAA.

        The created texture is also set as the active render target.

        Returns:
            The logical size ``(width, height)`` and the newly created target texture.
        """
        size = self._window_manager.size
        texture = Texture(
            self._renderer,
            (size[0] * self._ssaa, size[1] * self._ssaa),
            target=True,
            scale_quality=self._scale_quality,
        )
        self._renderer.target = texture
        return size, texture

    def update_target_texture(self) -> None:
        """Update the target texture from the current window size and SSAA.

        Call this method after the window size changes.
        """
        self._size, self._target_texture = self._recreate_target_texture()

    def create_font(self, path: pathlib.Path | str, size: int) -> pygame.font.Font:
        """Create a new font object.

        Args:
            path: Path to the font file.
            size: Font size in logical pixels.
                The actual font size is multiplied by the SSAA factor.

        Returns:
            A new ``pygame.font.Font`` object.

        Raises:
            FileNotFoundError: If ``path`` does not point to an existing file.
        """
        try:
            return pygame.font.Font(path, size * self._ssaa)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Font file not found: {path}.") from exc

    def create_texture(
        self,
        source: pathlib.Path | str | pygame.Surface | tuple[int, int],
        target: bool = False,
    ) -> Texture:
        """Create a new texture from an image file, surface, or size.

        Args:
            source: Path to the image file, ``pygame.Surface``,
                or texture size ``(width, height)``.
            target: Initialize the texture as target. Defaults to ``False``.

        Returns:
            A new texture object created from the image file, surface or size.

        Raises:
            FileNotFoundError: If ``source`` is a path that does not
                point to an existing file.
        """
        if isinstance(source, (tuple, list)):
            return Texture(
                self._renderer, source, target=target, scale_quality=self._scale_quality
            )
        if isinstance(source, pygame.Surface):
            return Texture.from_surface(self._renderer, source)
        try:
            return Texture.from_surface(self._renderer, pygame.image.load(source))
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Image file not found: {source}.") from exc

    def set_color(
        self, color: tuple[int, int, int] | tuple[int, int, int, int]
    ) -> None:
        """Set the draw color used by subsequent fill and clear operations.

        Args:
            color: A tuple representing the RGB/RGBA color values.
        """
        self._renderer.draw_color = color

    def clear(self) -> None:
        """Clear the render target."""
        self._renderer.clear()

    def present(
        self, destination: Texture | None = None, surface: pygame.Surface | None = None
    ) -> None:
        """Render the off-screen target texture into a destination render target.

        The off-screen texture stays the active render target afterward.

        Args:
            destination: Render target that receives the frame. If ``None``,
                the frame is presented to the window. Defaults to ``None``.
            surface: Optional surface that receives a software copy of the presented
                frame. If ``None``, no copy is made. Defaults to ``None``.
        """
        self._renderer.target = destination
        self._target_texture.draw(dstrect=(0.0, 0.0, self.width, self.height))
        self._renderer.present()
        if surface is not None:
            self._renderer.to_surface(surface=surface)
        self._renderer.target = self._target_texture

    def fill_quad(
        self,
        p1: tuple[float, float],
        p2: tuple[float, float],
        p3: tuple[float, float],
        p4: tuple[float, float],
    ) -> None:
        """Fill a quadrilateral.

        Args:
            p1: The first point of the quad ``(x, y)`` in logical pixels.
            p2: The second point of the quad ``(x, y)`` in logical pixels.
            p3: The third point of the quad ``(x, y)`` in logical pixels.
            p4: The fourth point of the quad ``(x, y)`` in logical pixels.
        """
        self._renderer.fill_quad(
            (p1[0] * self._ssaa, p1[1] * self._ssaa),
            (p2[0] * self._ssaa, p2[1] * self._ssaa),
            (p3[0] * self._ssaa, p3[1] * self._ssaa),
            (p4[0] * self._ssaa, p4[1] * self._ssaa),
        )

    def fill_rect(self, rect: tuple[float, float, float, float]) -> None:
        """Fill a rectangle.

        Args:
            rect: A tuple representing the rectangle ``(x, y, width, height)``
                in logical pixels.
        """
        self._renderer.fill_rect(
            (
                rect[0] * self._ssaa,
                rect[1] * self._ssaa,
                rect[2] * self._ssaa,
                rect[3] * self._ssaa,
            )
        )

    def draw_texture(
        self,
        texture: Texture,
        srcrect: tuple[float, float, float, float] | None = None,
        dstrect: tuple[float, float] | tuple[float, float, float, float] | None = None,
        angle: float = 0.0,
        origin: tuple[float, float] | None = None,
        flip_x: bool = False,
        flip_y: bool = False,
    ) -> None:
        """Draw the texture.

        Args:
            texture: The texture to draw.
            srcrect: The source rectangle ``(x, y, width, height)`` in texture pixels.
                Defaults to ``None``.
            dstrect: The destination rectangle ``(x, y, width, height)`` or its
                top-left position ``(x, y)`` in logical pixels. Defaults to ``None``.
            angle: The angle in degrees to rotate the texture.
                Defaults to ``0.0``.
            origin: The origin of the texture rotation ``(x, y)`` in logical pixels.
                Defaults to ``None``.
            flip_x: Whether the texture is horizontally flipped.
                Defaults to ``False``.
            flip_y: Whether the texture is vertically flipped.
                Defaults to ``False``.
        """
        if dstrect is not None:
            if len(dstrect) == 2:
                dstrect = (*dstrect, texture.width, texture.height)
            dstrect = (
                dstrect[0] * self._ssaa,
                dstrect[1] * self._ssaa,
                dstrect[2] * self._ssaa,
                dstrect[3] * self._ssaa,
            )
        if origin is not None:
            origin = (origin[0] * self._ssaa, origin[1] * self._ssaa)
        texture.draw(
            srcrect=srcrect,
            dstrect=dstrect,
            angle=angle,
            origin=origin,
            flip_x=flip_x,
            flip_y=flip_y,
        )

    def draw_text(
        self,
        lines: tuple[str, ...],
        font: pygame.font.Font,
        position: str,
        color: tuple[int, int, int] | tuple[int, int, int, int],
        offset: float,
        line_spacing: float,
    ) -> None:
        """Draw the text.

        Args:
            lines: Lines of text to draw.
            font: The font to use.
            position: The position of the text.
                Must be ``up-left``/``down-left``/``up-right``/``down-right``.
            color: A tuple representing the RGB/RGBA color values.
            offset: The distance from the corresponding render target edges
                in logical pixels.
            line_spacing: The line spacing multiplier. The vertical distance
                between lines is ``line_height * line_spacing``.

        Raises:
            ValueError: If ``position`` is not
                ``up-left``/``down-left``/``up-right``/``down-right``.
        """
        if position not in ("up-left", "down-left", "up-right", "down-right"):
            raise ValueError("Position must be up-left/down-left/up-right/down-right.")

        if "down" in position:
            lines = lines[::-1]
        for i, s in enumerate(lines):
            tex = self.create_texture(font.render(s, True, color))
            if "left" in position:
                x = offset * self._ssaa
            else:
                x = (self.width - offset) * self._ssaa - tex.width
            if "up" in position:
                y = offset * self._ssaa + i * tex.height * line_spacing
            else:
                y = (self.height - offset) * self._ssaa - (
                    i + 1
                ) * tex.height * line_spacing
            tex.draw(dstrect=(x, y))
