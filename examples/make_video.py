# RUN AS examples.make_video


from simulator import Sim, SimView

P_COEF = 12.0
I_COEF = 3
INTEGRAL_LIMIT = 1.2
D_COEF = 10.0

integral = 0.0


def regulator(x: float, target_x: float, v: float, step_integral: float) -> float:
    global integral

    deviation = x - target_x
    integral += step_integral
    integral = max(-INTEGRAL_LIMIT, min(integral, INTEGRAL_LIMIT))
    return -(deviation * P_COEF + integral * I_COEF + v * D_COEF)


def reset_callback() -> None:
    global integral

    integral = 0.0


sim = Sim(regulator, reset_callback=reset_callback, m=2.0, external_f=2.0, target_x=-1.5, x0=2.5, freq=1000.0, damping=0.5)
sim_view = SimView(sim, wind_size=(1920, 1080), speed=1, scale=0.15, font_size=30)
# sim_view.run()
sim_view.save_video(seconds=10, quality=40)
