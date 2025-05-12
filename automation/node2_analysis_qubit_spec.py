import nodeio
from qick import *
import matplotlib.pyplot as plt
import numpy as np
from tqdm.notebook import tqdm

from malab import *
from qubit_char_funcs import *
import json
from malab import *
from malab.dsfit import fitlor
from malab.dsfit import lorfunc
import time

import plotly.graph_objs as go
from send2web_kit import send_figure
from prompts import *

expt_name = "qubit_spec_ge"

# ==================== DEFINE NODE ====================

nodeio.context(
    name="Analysis_QSpec",
    description="finds rough qubit freq",
    icon="bootstrap/gear-fill.svg",
)

inputs = nodeio.Inputs()
inputs.stream("instructions",
              units="dictionary",
              description="dictionary: {experiment: ..., data:...}"
)

outputs = nodeio.Outputs()
outputs.define(
    "next",
    units="dictionary",
    description="dictionary: {experiment: ..., data:...}",
    retention=2,
)
outputs.define(
    "previous",
    units="dictionary",
    description="dictionary: {experiment: ..., data:...}",
    retention=2,
)
outputs.define(
    "repeat",
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

system_config['full_auto'] = FULL_AUTO
system_config['num_qubits'] = config['num_qubits']
system_config['qubit_index'] = config['qubit_index']
system_config['SS'] = config['SS']
system_config['MUX'] = config['MUX']

config = system_config

# set inputs data for dry-run of the node
with SlabFile(r'dummy_data/qubit_ge_spec.h5', 'r') as f:
    freqs = array(f['expt_pts'])[0][0]
    I = array(f['avgi'])[0]
    Q = array(f['avgq'])[0]
    mags = array(f['amps'])[0]
    fit_result = f.attrs['fit_result']
    fit_result = json.loads(fit_result)

inputs.set( instructions = {
    "experiment":config,
    "data": 'dummy_data/qubit_ge_spec.h5'
})

# =============== RUN NODE STATE MACHINE ===============
while nodeio.status.active:
    instructions = inputs.get("instructions")
    config = instructions["experiment"]
    data = instructions["data"]

    # QubitIndex = config["qubit_index"]  # qubit index

    ######################
    ###     Fiting     ###
    ######################
    ### USING QULANG_TOOLS ###
    # Use data file directly passed from last node
    with SlabFile(data, 'r') as f:
        # freqs = array(f['expt_pts'])[0][0] # for dry run
        freqs = array(f['fpts'])[0]
        I = array(f['avgi'])[0]
        Q = array(f['avgq'])[0]
        mags = array(f['amps'])[0]
        fit_result = f.attrs['fit_result']
        fit_result = json.loads(fit_result)
    
    f_q = fit_result['f']
    print('\n IF= %f +- %f MHz' % (f_q[0], f_q[1]))

    # parameters used to calculate fit equation
    kc = fit_result['kc'][0]
    k = fit_result['k'][0]
    offset = fit_result['offset'][0]
    y_fit = ((kc/k) / (1 + (4 * ((freqs - f_q[0]) ** 2) / (k ** 2)))) + offset

    fig = go.Figure()
    fig.update_xaxes(title_text='Freq (MHz)')
    fig.update_yaxes(title_text='Tramsmission (DAC Units)')
    fig.add_trace(go.Scatter(x=freqs, y=mags, mode='markers', name='data'))
    fig.add_trace(go.Scatter(x=freqs, y=y_fit, mode='lines', name='Fitted data'))
    fig.add_vline( x = f_q[0], line_width=1, line_dash="dash", line_color="Red")

    fitting_params = {'Resonance Freq (MHz)': f_q[0]}
    info_figure =  {
        'figure_json': fig.to_json(),
        'timestamp': time.time(),
        'fitting_params': fitting_params
    }
    response = send_figure('qubit_spec', info_figure)
    print('Plot send to web browser')
    print(response)

    # Update result after analysis
    analysis_result = {
        "freq": f_q[0],
    }

    if FULL_AUTO == 1:
        choice = 3
        config_new = config
        analysis_result_new = analysis_result

    else:
        # prompt for next step
        choice, config_new, analysis_result_new = process_node(analysis_result, config)

    # plt.close()
    ######################
    ###    Finishing   ###
    ######################

    if choice == 1:
        print("return to previous experiment")
        outputs.set(previous={
            "experiment": config,
            "data": []
        })

    elif choice == 2:
        print("repeating current experiment")
        outputs.set(repeat={
            "experiment": config_new,
            "data": []
        })

    elif choice == 3:
        print("proceed to next experiment")

        print(f"\n Old q{QUBIT_INDEX} freq", config["qubit_freq_ge"])
        config_new["qubit_freq_ge"] = analysis_result_new["freq"]
        print(f"\n New q{QUBIT_INDEX} pi freq",config_new["qubit_freq_ge"])
        print("\n Qubit spec analysis finished...")
        print("===================================")
        print("saving to file...")
        with SlabFile('output_data.hdf5', 'a') as f:
            f.append_pt("qubit_spec", config_new["qubit_freq_ge"])
            
        outputs.set(next={
            "experiment": config_new,
            "data": []
        })




