# RUN AS examples.pid_regulator


from simulator import Sim, SimView

P_COEF = 12.0
I_COEF = 1.5
D_COEF = 10.0

integral = 0.0


def regulator(x: float, target_x: float, v: float, step_integral: float) -> float:
    global integral

    deviation = x - target_x
    integral += step_integral
    return -(deviation * P_COEF + integral * I_COEF + v * D_COEF)


def reset_callback() -> None:
    global integral

    integral = 0.0


sim = Sim(regulator, reset_callback=reset_callback, m=2.0, external_f=2.0, x0=1.0, freq=10.0, damping=0.5)
sim_view = SimView(sim)
sim_view.run()
