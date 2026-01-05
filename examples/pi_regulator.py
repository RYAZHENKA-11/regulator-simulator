# RUN AS examples.pi_regulator


from simulator import Sim, SimView

P_COEF = 2.0
I_COEF = 1.0

integral = 0.0


def regulator(x: float, target_x: float, _v: float, step_integral: float) -> float:
    global integral

    deviation = x - target_x
    integral += step_integral
    return -(deviation * P_COEF + integral * I_COEF)


def reset_callback() -> None:
    global integral

    integral = 0.0


sim = Sim(regulator, reset_callback=reset_callback, m=0.5, external_f=1.0, x0=1.0, freq=20.0, damping=2.0)
sim_view = SimView(sim)
sim_view.run()
