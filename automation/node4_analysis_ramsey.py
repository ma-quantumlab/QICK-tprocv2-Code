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
from malab.dsfit import fitdecaysin
# from temp_fit import fitdecaysin, decaysin ## fix for scipy.fft issue

import plotly.graph_objs as go
from send2web_kit import send_figure
from prompts import *

# for fitting data
from qualang_tools.plot import Fit

expt_name = "Ramsey_ge"

# ==================== DEFINE NODE ====================

nodeio.context(
    name="Analysis_Ramsey",
    description="finds qubit freq and dephasing time",
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
with SlabFile(r'dummy_data/Ramsey_ge.h5', 'r') as f:
    expt_pts = array(f['expt_pts'])[0][0]
    times = array(f['times'])[0]
    I = array(f['avgi'])[0]
    Q = array(f['avgq'])[0]
    mags = array(f['amps'])[0]
    # ydata = array(f['ydata'])[0]
    pop_norm = array(f['pop_norm'])[0]
    fit_result = f.attrs['fit_result']
    fit_result = json.loads(fit_result)


inputs.set( instructions = {
    "experiment":config,
    "data": 'dummy_data/Ramsey_ge.h5'
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
        # expt_pts = array(f['expt_pts'])[0][0] # for dry run
        times = array(f['delay_times'])[0]
        # times = array(f['times'])[0] # for dry run
        I = array(f['avgi'])[0]
        Q = array(f['avgq'])[0]
        mags = array(f['amps'])[0]
        ydata = array(f['ydata'])[0]
        # pop_norm = array(f['pop_norm'])[0] # for dry run
        fit_result = f.attrs['fit_result']
        fit_result = json.loads(fit_result)
    
    with open('system_config.json', 'r') as f:
        target_freq = add_single_qubit_experiment(
            json.load(f)['expt_cfg'], expt_name,QUBIT_INDEX)['ramsey_freq']

    # ydata = pop_norm # for dry run

    # parameters used to calculate fit equation
    freq = fit_result['f'][0]*1e3
    phase = fit_result['phase'][0]
    t2 = fit_result['T2'][0]
    amp = fit_result['amp'][0]
    initial_offset = fit_result['initial_offset'][0]
    final_offset = fit_result['final_offset'][0]
    y_fit = final_offset * (1 - np.exp(-times * (1/t2))) + amp / 2 * (np.exp(-times * (1/t2))
            * (initial_offset * 2 + np.cos(2 * np.pi * freq/1e3 * times + phase)))


    print('\nDecay Time: %f +- %f ns' % (t2, fit_result['T2'][1]))
    print("\nOscillation frequency: %f +- %f MHz" % (freq, fit_result['f'][1]*1e3))

    fig = go.Figure()
    fig.update_xaxes(title_text='Variable delay [ns]')
    fig.update_yaxes(title_text='Population')
    fig.add_trace(go.Scatter(x=times, y=ydata, mode='markers', name='data'))
    fig.add_trace(go.Scatter(x=times, y=y_fit, mode='lines', name='Fitted data'))

    fitting_params = {'t2*(ns)': t2, 'detuning(MHz)': freq}
    info_figure = {
        'figure_json': fig.to_json(),
        'timestamp': time.time(),
        'fitting_params': fitting_params
    }
    response = send_figure('ramsey', info_figure)
    print('Plot send to web browser')
    print(response)

    # Update machine after analysis
    analysis_result = {
        "fit_detuning": freq,
        "fit_decay": t2
    }

    if FULL_AUTO == 1:
        if abs(freq - target_freq)<0.1:
            choice = 3
        else:
            choice = 1

        config_new = config
        analysis_result_new = analysis_result

    else:
        # prompt for next step
        choice, config_new, analysis_result_new = process_node(analysis_result, config)

    ######################
    ###    Finishing   ###
    ######################

    if choice == 1:
        print("return to previous experiment")
        print(f"\n Old q{QUBIT_INDEX} freq", config["qubit_freq_ge"])
        config["qubit_freq_ge"] = config["qubit_freq_ge"] \
                                 + target_freq\
                                 - analysis_result_new["fit_detuning"]
        config["t2"] = analysis_result_new["fit_decay"]

        print(f"\n New q{QUBIT_INDEX} freq", config["qubit_freq_ge"])
        print("\n Ramsey analysis finished...")
        print("===================================")

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
        config_new["qubit_freq_ge"] = config["qubit_freq_ge"] \
                                 + target_freq\
                                 - analysis_result_new["fit_detuning"]
        config_new["t2"] = analysis_result_new["fit_decay"]

        print(f"\n New q{QUBIT_INDEX} freq", config_new["qubit_freq_ge"])
        print("\n Ramsey analysis finished...")
        print("===================================")
        print("saving to file...")
        with SlabFile('output_data.hdf5', 'a') as f:
            f.append_pt("ramsey_freq_correction", config_new["qubit_freq_ge"])
            f.append_pt("ramsey_t2", config_new["t2"])

        outputs.set(next={
            "experiment": config_new,
            "data": []
        })
