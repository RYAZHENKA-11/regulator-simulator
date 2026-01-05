# RUN AS examples.pd_regulator


from simulator import Sim, SimView

P_COEF = 12.0
D_COEF = 8.5


def regulator(x: float, target_x: float, v: float, _step_integral: float) -> float:
    deviation = x - target_x
    return -(deviation * P_COEF + v * D_COEF)


sim = Sim(regulator, m=2.0, external_f=0.0, x0=4.0, freq=10.0, damping=0.5)
sim_view = SimView(sim)
sim_view.run()
