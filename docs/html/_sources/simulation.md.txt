# Simulation and KPI extraction

Loading a simulation model is as simple as:

```py
path = '../assets/config_base.xlsx'
wbook = oxl.load_workbook(path, data_only=True)
config = Config.from_workbook(wbook, sim_hours=10*168, num_reps=30, runner_speed=1.2)

model = Model(config)
model.run()
```

**Note:** despite the parameter `num_reps` in the {py:class}`.Config` class, `model.run()` only
runs the simulation once. Currently, running a simulation multiple times requires writing
your own `for` loop.

Specimen attributes can be collected from `model.specimen_data`, and includes timestamp information
from which turnaround times can be computed. For example:

```py
import numpy as np

overall_tats = [v['reporting_end']-v['reception_start']
            for v in model.specimen_data.values() if 'qc_end' in v]

lab_tats = [v['qc_end']-v['reception_start']
            for v in model.specimen_data.values() if 'qc_end' in v]
lab_tats = lab_tats/24.
print(
    np.mean(lab_tats),  # mean lab TAT
    np.array([
        np.mean(lab_tats < n) for n in range(28)
    ])  # Proportion of specimens completed in n days
)
```

The resources defined in the simulation are accessible via {py:attr}`.Model.resources`, and thanks
to the `salabim` library have their own built-in statisics collection. For example, given a
`Resource` named `res`, we can compute the mean utilisation as:

```py
mean_util = res.claimed_quanity.mean() / res.capacity.mean()
```
