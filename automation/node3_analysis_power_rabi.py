import nodeio
from qick import *
import matplotlib.pyplot as plt
import numpy as np
from tqdm.notebook import tqdm

from malab import *
from qubit_char_funcs import *
import json
import time
from malab import *
from malab.dsfit import fitlor,fitsin
# from temp_fit import fitdecaysin, decaysin ## fix for scipy.fft issue

import plotly.graph_objs as go
from send2web_kit import send_figure
from prompts import *

expt_name = "power_rabi_ge"

# ==================== DEFINE NODE ====================

# for fitting data
from qualang_tools.plot import Fit

nodeio.context(
    name="Analysis_Prabi",
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
with SlabFile(r'dummy_data/power_rabi_ge.h5', 'r') as f:
    power = array(f['expt_pts'])[0][0]
    I = array(f['avgi'])[0]
    Q = array(f['avgq'])[0]
    # ydata = array(f['ydata'])[0]
    mags = array(f['amps'])[0]
    pop_norm = array(f['pop_norm'])[0]
    fit_result = f.attrs['fit_result']
    fit_result = json.loads(fit_result)


inputs.set( instructions = {
    "experiment":config,
    "data": 'dummy_data/power_rabi_ge.h5'
})

# =============== RUN NODE STATE MACHINE ===============

while nodeio.status.active:
    instructions = inputs.get("instructions")
    config = instructions["experiment"]
    data = instructions["data"]

    # QubitIndex = config["qubit_index"]  # qubit index

    ######################
    ###     Fitting    ###
    ######################
    ### USING QULANG_TOOLS ###
    # Use data file directly passed from last node
    with SlabFile(data, 'r') as f:
        power = array(f['gains'])[0]
        # power = array(f['expt_pts'])[0][0] # for dry run
        I = array(f['avgi'])[0]
        Q = array(f['avgq'])[0]
        ydata = array(f['ydata'])[0]
        mags = array(f['amps'])[0]
        # pop_norm = array(f['pop_norm'])[0] # for dry run
        fit_result = f.attrs['fit_result']
        fit_result = json.loads(fit_result)
    
    # ydata = pop_norm # for dry run

    # parameters used to calculate fit equation
    freq = fit_result['f'][0]
    phase = fit_result['phase'][0]
    T = fit_result['T'][0]
    amp = fit_result['amp'][0]
    offset = fit_result['offset'][0]
    y_fit = amp * (np.sin(0.5 * (2 * np.pi * freq) * power + phase))**2 * np.exp(-power / T) + offset
    fit_std = (ydata - y_fit).std()

    peak = 0.5 / freq
    print("\n fitting error = ",fit_std )
    print('\n peak amp at %f' % (peak))

    fig = go.Figure()
    fig.update_xaxes(title_text='Amps')
    fig.update_yaxes(title_text='Population')
    fig.add_trace(go.Scatter(x=power, y=ydata, mode='markers', name='data'))
    fig.add_trace(go.Scatter(x=power, y=y_fit, mode='lines', name='Fitted data'))
    fig.add_vline(x=peak, line_width=1, line_dash="dash", line_color="Red")

    fitting_params = {'pi pulse amp': peak}
    info_figure = {
        'figure_json': fig.to_json(),
        'timestamp': time.time(),
        'fitting_params': fitting_params
    }
    response = send_figure('rabi', info_figure)
    print('Plot send to web browser')
    print(response)

    # Update machine after analysis
    analysis_result = {
        "peak": peak,
    }

    if FULL_AUTO == 1 and fit_std<0.5:
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

        print(f"\n Old q{QUBIT_INDEX} pi-pulse amp", config["qubit_gain_ge"])
        config_new["qubit_gain_ge"] = analysis_result_new["peak"]
        # config_new["config"]["qubit_cfg"]["pi2_ge_gain"] = analysis_result_new["peak"]/2
        print(f"\n New q{QUBIT_INDEX} pi-pulse amp", config_new["qubit_gain_ge"])
        print("\n Power rabi analysis finished...")
        print("===================================")
        print("saving to file...")
        with SlabFile('output_data.hdf5', 'a') as f:
            f.append_pt("power_rabi", config_new["qubit_gain_ge"])

        outputs.set(next={
            "experiment": config_new,
            "data": []
        })

