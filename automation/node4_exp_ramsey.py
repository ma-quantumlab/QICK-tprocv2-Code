import nodeio
from qick import *
import matplotlib.pyplot as plt
import numpy as np
from tqdm.notebook import tqdm

from malab import *
import json
import time

from qualang_tools.plot import Fit

from build_task import *
from build_state import *
from qubit_char_funcs import * # also connects to rfsoc

with open('system_config.json', 'r') as f:
    data_path = json.load(f)['DATA_PATH']

expt_name = "Ramsey_ge"

# ==================== DEFINE NODE ====================

nodeio.context(name="Exp_Ramsey",
               description="Ramsey",
               icon="bootstrap/gear-fill.svg"
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

with open('system_config.json', 'r') as f:
    exp_config = add_single_qubit_experiment(json.load(f)['expt_cfg'], expt_name, config['qubit_index'])

inputs.set( instructions = {
    "experiment":config,
    "data": []
})

# =============== RUN NODE STATE MACHINE ===============
"""
performs ramsey with a single shot experiment after
"""
while nodeio.status.active:

    instructions = inputs.get("instructions")
    config = instructions["experiment"]
    # exp_config = instructions["experiment"]["expt_cfg"]
    # QubitIndex = config["qubit_index"]  # qubit index

    print('System Configurations:')
    print(config)
    print("Experiment Configurations:")
    print(exp_config)

    print("===================================")
    print("Doing ramsey...")
    start_time = time.time()

    ###############
    # The program #
    ###############

    ### RAMSEY ###
    # ----- Experiment configurations ----- #
    ramsey_config = {**config, **exp_config}
    
    # --- Acquires the data and runs the program --- #
    ramsey=RamseyProgram(soccfg, reps=ramsey_config['reps'], final_delay=ramsey_config['relax_delay'], cfg=ramsey_config)
    py_avg = ramsey_config['py_avg']

    # for live plotting
    IS_VISDOM = True
    if IS_VISDOM:
        expt_I = expt_Q = expt_mags = expt_phases = expt_pop = None
        viz = visdom.Visdom()
        assert viz.check_connection(timeout_seconds=5), "Visdom server not connected!"
        viz.close(win=None) # close previous plots
        win1 = viz.line( X=np.arange(0, 1), Y=np.arange(0, 1),
            opts=dict(height=400, width=700, title='T2 Ramsey Experiment', showlegend=True, xlabel='expt_pts'))

        for ii in range(py_avg):
            iq_list = ramsey.acquire(soc, soft_avgs=1, progress=False)
            delay_times = ramsey.get_time_param('wait', "t", as_array=True)

            iq_list = iq_list[0][0].T
            # what is the correct shape/index?
            this_I = (iq_list[0])
            this_Q = (iq_list[1])

            if expt_I is None: # ii == 0
                expt_I, expt_Q = this_I, this_Q
            else:
                expt_I = (expt_I * ii + this_I) / (ii + 1.0)
                expt_Q = (expt_Q * ii + this_Q) / (ii + 1.0)

            expt_mags = np.abs(expt_I + 1j * expt_Q)  # magnitude
            expt_phases = np.angle(expt_I + 1j * expt_Q)  # phase

            viz.line(X = delay_times, Y = expt_mags, win=win1, name='I',
            opts=dict(height=400, width=700, title='T2 Ramsey Experiment', showlegend=True, xlabel='expt_pts'))


        amps = expt_mags
        
    else:
        iq_list = ramsey.acquire(soc, soft_avgs=py_avg, progress=True)
        delay_times = ramsey.get_time_param('wait', "t", as_array=True)
        amps = np.abs(iq_list[0][0].dot([1,1j]))

    print("Ramsey finished...")
    print(time.time() - start_time, ' s')
    print("===================================")
    
    ### SINGLE SHOT ###
    if SS == 'True':
        print('performing single shot for g-e calibration')
        start_time = time.time()

        # ss_config, expt_name = initialize_configs("IQ_plot")
        with open('system_config.json', 'r') as f:
            ss_config = {**config, 
                **add_single_qubit_experiment(
                    json.load(f)['expt_cfg'], 'IQ_plot',QUBIT_INDEX)}

        # ss_config = {**config, **exp_config["IQ_plot"]}

        ssp_g = SingleShotProgram_g(soccfg, reps=1, final_delay=ss_config['relax_delay'], cfg=ss_config)
        iq_list_g = ssp_g.acquire(soc, soft_avgs=1, progress=True)

        ssp_e = SingleShotProgram_e(soccfg, reps=1, final_delay=ss_config['relax_delay'], cfg=ss_config)
        iq_list_e = ssp_e.acquire(soc, soft_avgs=1, progress=True)

        Ig = iq_list_g[0][0].T[0]
        Qg = iq_list_g[0][0].T[1]
        Ie = iq_list_e[0][0].T[0]
        Qe = iq_list_e[0][0].T[1]
        
        print("Single shot finished...")
        print(time.time() - start_time, ' s')
        print("===================================")

    print("Fitting data...")
    ### Fit ###
    fit = Fit()
    
    # Normalize data
    if SS == 'True':
        # Normalize data
        e = np.mean((Ie+1j*Qe))
        g = np.mean((Ig+1j*Qg))
        ### Normalization ###
        pop_norm = abs(((expt_I+1j*expt_Q) - g)*(e - g) / abs(e - g)**2)
        ydata = pop_norm
    else:
        ydata = amps

    delay_times *= 1e3 # convert form us to ns

    # Choose the suitable fitting function
    fit_result = fit.ramsey(delay_times, ydata)

    fit_result = {
            "f": fit_result['f'],
            "phase": fit_result['phase'],
            "T2": fit_result['T2'],
            "amp": fit_result['amp'],
            "initial_offset": fit_result['initial_offset'],
            "final_offset": fit_result['final_offset']
        }
    
    ramsey_config['t2'] = fit_result['T2'][0]
    time.sleep(10)

    #####################################
    # ----- Saves data to a file ----- #
    #####################################

    prefix = str(datetime.date.today())
    exp_name = expt_name + '_Q' + str(QUBIT_INDEX) + '_' + prefix
    print('Experiment name: ' + exp_name)

    fname = get_next_filename(data_path, exp_name, suffix='.h5')
    print('Current data file: ' + fname)

    with SlabFile(data_path + '\\' + fname, 'a') as f:
        # 'a': read/write/create

        # - Adds data to the file - #
        f.append('delay_times', delay_times)
        f.append('amps', amps)
        f.append('ydata', ydata)
        if IS_VISDOM:
            f.append('avgi', expt_I)
            f.append('avgq', expt_Q)
        else:
            f.append('avgi', iq_list[0][0].T[0])
            f.append('avgq', iq_list[0][0].T[1])

        del ramsey_config['wait_time']  # cant save QickParam
        # formats config into file as a single line
        f.attrs['config'] = json.dumps(ramsey_config)
        f.attrs['fit_result'] = json.dumps(fit_result)

        if SS == 'True':
            # - Adds ss data to the file - #
            f.append('I_g', Ig)
            f.append('Q_g', Qg)
            f.append('I_e', Ie)
            f.append('Q_e', Qe)    

            # formats config into file as a single line
            f.attrs['ss_config'] = json.dumps(ss_config)
        

    data = data_path + '\\' + fname

    # send to output, data need to be list type
    outputs.set(next={
        "experiment": instructions["experiment"],
        "data": data
    })
    # todo: data can also be saved as a dictionary format