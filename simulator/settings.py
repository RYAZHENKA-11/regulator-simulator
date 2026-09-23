"""Settings management for the simulator application."""

import json
from dataclasses import asdict, dataclass

SETTINGS_FILE: str = ".settings.json"


@dataclass
class Settings:
    """Container for application settings.

    Attributes:
        window_size: Window size for ``WindowManager``. Defaults to ``(640, 480)``.
        window_position: Window position for ``WindowManager``. Defaults to ``(0, 0)``.
        scale: Scale for ``SimulationRenderer``. Defaults to ``0.1``.
        speed: Speed for ``PlayerController`` and ``VideoExporter``.
            Defaults to ``1.0``.
    """

    window_size: tuple[int, int] = (640, 480)
    window_position: tuple[int, int] = (0, 0)
    scale: float = 0.1
    speed: float = 1.0

    def save(self, path: str = SETTINGS_FILE) -> None:
        """Save current settings to a JSON file.

        Args:
            path: Path to the settings file. Defaults to ``SETTINGS_FILE``.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    def load(self, path: str = SETTINGS_FILE) -> None:
        """Load settings from a JSON file.

        Args:
            path: Path to the settings file. Defaults to ``SETTINGS_FILE``.

        Raises:
            TypeError: If the file is not a JSON object or contains a setting
                with an unexpected type.
        """
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Settings file '{path}' not found. Using default settings.")
            return

        if not isinstance(data, dict):
            raise TypeError(
                f"Settings file must contain a JSON object, got {type(data).__name__}."
            )

        known = {key: value for key, value in data.items() if hasattr(self, key)}
        parsed = {key: self._parse_value(key, value) for key, value in known.items()}
        for key, value in parsed.items():
            setattr(self, key, value)

    @classmethod
    def _parse_value(cls, key: str, value: object) -> object:
        """Validate and coerce a field value to its expected type.

        Args:
            key: Field name.
            value: Field value.

        Returns:
            The field value coerced to its expected type.

        Raises:
            TypeError: If the field value is an unexpected type.
        """
        if key in ("window_size", "window_position"):
            if (
                not isinstance(value, (list, tuple))
                or len(value) != 2
                or any(
                    not isinstance(axis, int) or isinstance(axis, bool)
                    for axis in value
                )
            ):
                raise TypeError(f"{key} must be a pair of integers, got {value!r}.")
            return tuple(value)
        if key in ("scale", "speed"):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{key} must be a number, got {value!r}.")
            return float(value)
        return value
