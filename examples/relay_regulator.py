# RUN AS examples.relay_regulator


from simulator import Sim, SimView

CONTROL_FORCE = 10.0


def regulator(x: float, target_x: float, _v: float, _step_integral: float) -> float:
    deviation = x - target_x
    if deviation > 0:
        return -CONTROL_FORCE
    elif deviation == 0:
        return 0.0
    else:
        return CONTROL_FORCE


sim = Sim(regulator, m=0.5, external_f=0.0, x0=1.0, freq=100.0, damping=10.0)
sim_view = SimView(sim)
sim_view.run()
