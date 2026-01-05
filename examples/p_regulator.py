# RUN AS examples.p_regulator


from simulator import Sim, SimView

P_COEF = 3.0


def regulator(x: float, target_x: float, _v: float, _step_integral: float) -> float:
    deviation = x - target_x
    return -(deviation * P_COEF)


sim = Sim(regulator, m=0.5, external_f=0.0, x0=1.5, freq=20.0, damping=2.0)
sim_view = SimView(sim)
sim_view.run()
