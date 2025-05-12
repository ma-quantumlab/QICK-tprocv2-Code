# ==================== DEFINE NODE ====================
import nodeio
from qick import *
import matplotlib.pyplot as plt
import numpy as np
from tqdm.notebook import tqdm

from malab import *
# from automated_qubit_char_rfsoc.automation.qubit_char_funcs import *
import json

nodeio.context(
    name="Exp_Exit",
    description="node - exit",
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
with open('system_config.json', 'r') as f:
    configs = json.load(f)

inputs.set( instructions = {
    "experiment":configs,
    "data": []
})
# =============== RUN NODE STATE MACHINE ===============

while nodeio.status.active:

    instructions = inputs.get("instructions")
    configs = instructions["experiment"]

    # do some experiment with machine

    outputs.set(next={
        "experiment": configs,
        "data":[]
    })
    print("===================================")
    print("Workflow is finished")
    print("===================================")
    # if last experiment
    nodeio.terminate_workflow()