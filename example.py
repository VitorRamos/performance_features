from performance_features import Profiler
import pandas as pd

try:
    evs_monitor = [["PERF_COUNT_HW_INSTRUCTIONS"], ["SYSTEMWIDE:RAPL_ENERGY_PKG"]]
    program = Profiler(program_args=["./tests/simple_bench"], events_groups=evs_monitor)
    data = program.run(sample_period=0.01, reset_on_sample=False)
    df = pd.DataFrame(data, columns=["inst", "energy"])
    df["energy"] *= 2.3283064365386962890625e-10
    print(df)
except RuntimeError as e:
    print(e.args[0])
