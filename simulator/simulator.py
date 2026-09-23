"""Simulator for a mass–damper system driven by a regulator callback."""

import math
from collections.abc import Callable


class Simulator:
    """Simulator for a mass–damper system driven by a regulator callback.

    Attributes:
        regulator: ``Callable`` that computes the control force.
            It is invoked once per regulator step with the signature
            ``(x, target_x, v, step_integral) -> f``, where:
            ``x`` is the current position in meters,
            ``target_x`` is the target position in meters,
            ``v`` is the current velocity in meters/second,
            ``step_integral`` is an integral of position deviation
            accumulated since the last regulator invocation, in meter-seconds (m·s),
            ``f`` is the control force in newtons.
        reset_callback: ``Callable`` that resets the regulator's internal state.
            If ``None``, no callback is invoked.
        external_f: Constant external force along the x-axis in newtons.
        target_x: Target position in meters.
        x0: Initial position in meters.
        v0: Initial velocity in meters/second.
        f0: Initial control force in newtons.
        m: System mass in kilograms. Must be positive.
        damping: Viscous damping coefficient in newton-seconds per meter (N·s/m).
            Must be non-negative.
        freq: Regulator sampling rate in Hz. Must be positive. Read-only.
        x: Current position in meters. Read-only.
        v: Current velocity in meters/second. Read-only.
        f: Current control force in newtons. Read-only.
    """

    regulator: Callable[[float, float, float, float], float]
    reset_callback: Callable[[], None] | None
    external_f: float
    target_x: float
    x0: float
    v0: float
    f0: float

    _m: float
    _damping: float
    _freq: float
    _dt: float
    _x: float
    _v: float
    _f: float
    _time_after_last_step: float
    _step_integral: float

    def __init__(
        self,
        regulator: Callable[[float, float, float, float], float],
        reset_callback: Callable[[], None] | None = None,
        m: float = 1.0,
        damping: float = 1.0,
        external_f: float = 1.0,
        freq: float = 100.0,
        target_x: float = -1.0,
        x0: float = 1.0,
        v0: float = 0.0,
        f0: float = 0.0,
    ) -> None:
        """Initialize the simulator system.

        Args:
            regulator: Callable that computes the control force.
                It is invoked once per regulator step with the signature
                ``(x, target_x, v, step_integral) -> f``, where:
                ``x`` is the current position in meters,
                ``target_x`` is the target position in meters,
                ``v`` is the current velocity in meters/second,
                ``step_integral`` is an integral of position deviation
                accumulated since the last regulator invocation, in meter-seconds (m·s),
                ``f`` is the control force in newtons.
            reset_callback: Callable that resets the regulator's internal state.
                If ``None``, no callback is invoked. Defaults to ``None``.
            m: System mass in kilograms. Must be positive. Defaults to ``1.0``.
            damping: Viscous damping coefficient in newton-seconds per meter (N·s/m).
                Must be non-negative. Defaults to ``1.0``.
            external_f: Constant external force along the x-axis in newtons.
                Defaults to ``1.0``.
            freq: Regulator sampling rate in Hz. Must be positive.
                Defaults to ``100.0``.
            target_x: Target position in meters. Defaults to ``-1.0``.
            x0: Initial position in meters. Defaults to ``1.0``.
            v0: Initial velocity in meters/second. Defaults to ``0.0``.
            f0: Initial control force in newtons. Defaults to ``0.0``.

        Raises:
            ValueError: If ``m`` is not positive, ``damping`` is negative,
                or ``freq`` is not positive.
        """
        if freq <= 0.0:
            raise ValueError("Regulator sampling rate must be positive.")

        self.regulator = regulator
        self.reset_callback = reset_callback
        self.m = m
        self.damping = damping
        self.external_f = external_f
        self._freq = freq
        self._dt = 1.0 / freq
        self.target_x = target_x
        self.x0 = x0
        self.v0 = v0
        self.f0 = f0
        self.reset()

    @property
    def m(self) -> float:
        """System mass in kilograms."""
        return self._m

    @m.setter
    def m(self, m: float) -> None:
        """Set the system mass in kilograms. Must be positive.

        Raises:
            ValueError: If ``m`` is not positive.
        """
        if m <= 0.0:
            raise ValueError("Mass must be positive.")
        self._m = m

    @property
    def damping(self) -> float:
        """Viscous damping coefficient in newton-seconds per meter (N·s/m)."""
        return self._damping

    @damping.setter
    def damping(self, damping: float) -> None:
        """Set the viscous damping coefficient in newton-seconds per meter (N·s/m).
        Must be non-negative.

        Raises:
            ValueError: If ``damping`` is negative.
        """
        if damping < 0.0:
            raise ValueError("Damping must be non-negative.")
        self._damping = damping

    @property
    def freq(self) -> float:
        """Regulator sampling rate in Hz."""
        return self._freq

    @property
    def x(self) -> float:
        """Current position in meters."""
        return self._x

    @property
    def v(self) -> float:
        """Current velocity in meters/second."""
        return self._v

    @property
    def f(self) -> float:
        """Current control force in newtons."""
        return self._f

    def _advance(self, dt: float) -> None:
        """Integrate the system dynamics over ``dt`` seconds.

        Args:
            dt: Time interval to advance in seconds. Must be non-negative.

        Raises:
            ValueError: If ``dt`` is negative.
        """
        if dt < 0.0:
            raise ValueError("Time interval must be non-negative.")

        if math.isclose(self.damping, 0.0):
            a = (self.f + self.external_f) / self.m
            new_v = self.v + a * dt
            new_x = self.x + self.v * dt + 0.5 * a * dt * dt
            self._step_integral += (
                (self.x - self.target_x) * dt
                + 0.5 * self.v * dt * dt
                + a * dt * dt * dt / 6.0
            )
        else:
            tau = self.m / self.damping
            v_term = (self.f + self.external_f) / self.damping
            exp_factor = math.exp(-dt / tau)
            new_v = v_term + (self.v - v_term) * exp_factor
            new_x = self.x + v_term * dt + tau * (self.v - v_term) * (1.0 - exp_factor)
            self._step_integral += (
                (self.x - self.target_x) * dt
                + 0.5 * v_term * dt * dt
                + tau * (self.v - v_term) * (dt - tau * (1.0 - exp_factor))
            )
        self._x = new_x
        self._v = new_v
        self._time_after_last_step += dt

    def _apply_regulator(self) -> None:
        """Invoke the regulator and reset the step integral."""
        self._f = self.regulator(self.x, self.target_x, self.v, self._step_integral)
        self._step_integral = 0.0

    def simulate_step(self) -> None:
        """Advance the simulation by exactly one regulator step."""
        self._advance(self._dt - self._time_after_last_step)
        self._apply_regulator()
        self._time_after_last_step = 0.0

    def simulate_steps(self, steps: int) -> None:
        """Advance the simulation by the given number of regulator steps.

        Args:
            steps: Number of regulator steps to simulate.
                Must be a non-negative integer.

        Raises:
            ValueError: If ``steps`` is negative or not an integer.
        """
        if not isinstance(steps, int) or isinstance(steps, bool) or steps < 0:
            raise ValueError("Steps to simulate must be a non-negative integer.")

        for _ in range(steps):
            self.simulate_step()

    def simulate_dt(self, dt: float) -> None:
        """Advance the simulation by ``dt`` seconds.

        Args:
            dt: Time interval to simulate in seconds. Must be non-negative.

        Raises:
            ValueError: If ``dt`` is negative.
        """
        if dt < 0.0:
            raise ValueError("Time interval must be non-negative.")

        need_dt = self._dt - self._time_after_last_step
        if dt < need_dt:
            self._advance(dt)
            return
        self.simulate_step()
        dt -= need_dt
        self.simulate_steps(int(dt / self._dt))
        self._advance(dt % self._dt)

    def reset(self) -> None:
        """Reset the simulator and the regulator to their initial state."""
        self._x = self.x0
        self._v = self.v0
        self._f = self.f0
        self._time_after_last_step = 0.0
        self._step_integral = 0.0
        if self.reset_callback is not None:
            self.reset_callback()
