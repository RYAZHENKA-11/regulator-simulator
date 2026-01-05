import math
from typing import Callable, Optional

RegulatorFunc = Callable[[float, float, float, float], float]


class Sim:
    """
    Regulator simulator for physical system with mass and damping.
    Uses analytical solution for motion equations.
    """

    def __init__(
            self,
            regulator: RegulatorFunc,
            reset_callback: Optional[Callable[[], None]] = None,
            m: float = 1.0,
            damping: float = 1.0,
            external_f: float = 1.0,
            freq: float = 100.0,
            target_x: float = 0.0,
            x0: float = 1.0,
            v0: float = 0.0,
            f0: float = 0.0
    ) -> None:
        """
        Initialize the simulator system.

        Args:
            regulator: Function that calculates control force:
                (x, target_x, v, step_integral) -> f
                x: Current position (m)
                target_x: Target position (m)
                v: Current velocity (m/s)
                step_integral: Integral of position deviation over the last regulator step (m)
            reset_callback: Function that resets regulator state
            m: System mass (kg)
            damping: Damping coefficient (N·s/m)
            external_f: Constant external force (N)
            freq: Regulator sampling rate (Hz)
            target_x: Target position (m)
            x0: Initial position (m)
            v0: Initial velocity (m/s)
            f0: Initial force (N)
        """
        if freq <= 0:
            raise ValueError("Sampling frequency must be positive")

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

        self._x = 0.0
        self._v = 0.0
        self._f = 0.0
        self._time_after_last_step = 0.0
        self._step_integral = 0.0
        self.reset()

    @property
    def m(self) -> float:
        """Getter: returns the m value."""
        return self._m

    @m.setter
    def m(self, m: float) -> None:
        """Setter: adds validation logic."""
        if m <= 0:
            raise ValueError("Mass must be positive")
        self._m = m

    @property
    def damping(self) -> float:
        """Getter: returns the damping value."""
        return self._damping

    @damping.setter
    def damping(self, damping: float) -> None:
        """Setter: adds validation logic."""
        if damping < 0:
            raise ValueError("Damping cannot be negative")
        self._damping = damping

    @property
    def freq(self) -> float:
        """Getter: returns the freq value."""
        return self._freq

    @property
    def x(self) -> float:
        """Getter: returns the x value."""
        return self._x

    @property
    def v(self) -> float:
        """Getter: returns the v value."""
        return self._v

    @property
    def f(self) -> float:
        """Getter: returns the f value."""
        return self._f

    def _calc_while_dt(self, dt: float) -> None:
        """
        Calculate system state for amount dt.

        Args:
            dt: time to simulate
        """
        if math.isclose(self._damping, 0.0):
            a = (self.f + self.external_f) / self.m

            new_v = (self.v
                     + a * dt)
            new_x = (self.x
                     + self.v * dt
                     + 0.5 * a * dt * dt)
            self._step_integral += ((self.x - self.target_x) * dt
                                    + 0.5 * self.v * dt * dt
                                    + a * dt * dt * dt / 6)
        else:
            tau = self.m / self._damping
            v_term = (self.f + self.external_f) / self._damping
            exp_factor = math.exp(-dt / tau)

            new_v = (v_term
                     + (self.v - v_term) * exp_factor)
            new_x = (self.x
                     + v_term * dt
                     + tau * (self.v - v_term) * (1 - exp_factor))
            self._step_integral += ((self.x - self.target_x) * dt
                                    + 0.5 * v_term * dt * dt
                                    + tau * (self.v - v_term) * (dt - tau * (1 - exp_factor)))
        self._x = new_x
        self._v = new_v
        self._time_after_last_step += dt

    def _apply_regulator(self) -> None:
        """Calculate force."""
        self._f = self.regulator(self.x, self.target_x, self.v, self._step_integral)
        self._step_integral = 0

    def simulate_dt(self, seconds: float) -> None:
        """
        Calculate system state for amount seconds.

        Args:
            seconds: Seconds to simulate
        """
        if seconds < 0:
            raise ValueError("Seconds cannot be negative")

        need_dt = self._dt - self._time_after_last_step
        if seconds < need_dt:
            self._calc_while_dt(seconds)
            return
        self.simulate_step()
        seconds -= need_dt
        self.simulate_steps(int(seconds / self._dt))
        self._calc_while_dt(seconds % self._dt)

    def simulate_step(self) -> None:
        """Calculate system state for one regulator step."""
        self._calc_while_dt(self._dt - self._time_after_last_step)
        self._apply_regulator()
        self._time_after_last_step = 0

    def simulate_steps(self, amount: int) -> None:
        """
        Calculate system state for amount regulator steps.

        Args:
            amount: Amount of regulator steps to simulate
        """
        if amount < 0:
            raise ValueError("Amount cannot be negative")

        for i in range(amount):
            self.simulate_step()

    def reset(self) -> None:
        """Resets the simulator state."""
        self._x = self.x0
        self._v = self.v0
        self._f = self.f0
        self._time_after_last_step = 0
        self._step_integral = 0
        if self.reset_callback is not None:
            self.reset_callback()
