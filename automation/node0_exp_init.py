import nodeio
from qick import *
import matplotlib.pyplot as plt
import numpy as np
from tqdm.notebook import tqdm

from malab import *
import json

from build_task import *
from build_state import *
from qubit_char_funcs import * # also connects to rfsoc

# ==================== DEFINE NODE ====================

nodeio.context(
    name="Exp_Init",
    description="node 0 - initial",
    icon="bootstrap/gear-fill.svg",
)

inputs = nodeio.Inputs()
inputs.stream(
    "instructions",
    units="dictionary",
    description="",
)

# define outputs
outputs = nodeio.Outputs()
outputs.define(
    "next",
    units="dictionary",
    description="dictionary: {experiment: ..., data:...}",
    retention=2,
)
nodeio.register()

# ==================== DRY RUN DATA ====================

# needed just for repeated for development with repeated runs in IPython
inputs.reset_all_dry_run_data()

# set inputs data for dry-run of the node
inputs.set(instructions={
    "experiment": "system_config.json",
    "data": []
})

# =============== RUN NODE STATE MACHINE ===============

while nodeio.status.active:
    instructions = inputs.get("instructions")

    with open(instructions["experiment"], 'r') as f:
        configs = json.load(f)
    
    config = configs['config']
    # set configurations for correct QubitIndex

    if config['MUX'] == 'True': # MUX experiments        
        hw_cfg_cpy = add_qubit_channel(config, config['qubit_index'])
        qubit_cfg_cpy = add_qubit_cfg(config, config['qubit_index'])
        system_config = {**hw_cfg_cpy, **qubit_cfg_cpy, **readout_cfg}
        expt_name = expt_name + '_mux'
    else: # non-MUX experiments
        q_config = all_qubit_state(config)
        system_config = {**q_config['Q' + str(config['qubit_index'])]}
    
    # exp_cfg = SingleQubitAllExperimentParameter()
    
    # expt_config = {
    #     "config": system_config, 
    #     "expt_cfg": exp_cfg
    #     }

    # do some experiment with machine
    print("zcu216 configuration:")
    print(soccfg)

    outputs.set(next={
        "experiment": system_config,
        "data":[]
    })
