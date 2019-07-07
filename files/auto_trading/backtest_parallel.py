import subprocess
import time
from math import ceil


all_parameters_gen = iter(range(0,  1000))
batch_size = 24
py_script_path="/home/zadegan/rolling_opt.py"

bailout = False
while True:
    current_params_batch = []
    for i in range(0,batch_size):
        try:
            current_params_batch.append(next(all_parameters_gen))
        except StopIteration:
            bailout = True
            break
    processes = []
    for params in current_params_batch:
        # check for
        p = subprocess.Popen(
            [
                '/home/zadegan/backtest_env/bin/python3',
                py_script_path,
                "{}".format(params)
            ]
        )
        processes.append(p)
    for p in processes:
        p.wait()
    if bailout:
        break





