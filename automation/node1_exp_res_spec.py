import nodeio
from qick import *
import matplotlib.pyplot as plt
import numpy as np
from tqdm.notebook import tqdm

from malab import *
import json
import time
import numpy as np

from qualang_tools.plot import Fit

from build_task import *
from build_state import *
from qubit_char_funcs import * # also connects to rfsoc

with open('system_config.json', 'r') as f:
    data_path = json.load(f)['DATA_PATH']

expt_name = "res_spec_ge"

# ==================== DEFINE NODE ====================

nodeio.context(name="Exp_Rspec",
               description="resonator spectroscopy",
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
performs the 1D resonator spectroscopy
"""
while nodeio.status.active:

    instructions = inputs.get("instructions")
    config = instructions["experiment"]
    # exp_config = instructions["experiment"]["expt_cfg"]
    # print(config)
    # QubitIndex = config["qubit_index"]  # qubit index

    print('System Configurations:')
    print(config)
    print("Experiment Configurations:")
    print(exp_config)
    
    print("===================================")
    print("Doing resonator spectroscopy...")
    start_time = time.time()
    ###############
    # The program #
    ###############

    # --- Combines Experiment configurations --- #
    config = {**config, **exp_config}
    print(config)
    # --- Acquires the data and runs program--- #
    if MUX == 'False': # non-MUX program
        prog = SingleToneSpectroscopyProgram(soccfg, reps=config['reps'], final_delay=config['relax_delay'], cfg=config)
        py_avg = config['py_avg']

        # for live plotting
        IS_VISDOM = True
        if IS_VISDOM:
            expt_I = expt_Q = expt_mags = expt_phases = expt_pop = None
            viz = visdom.Visdom()
            assert viz.check_connection(timeout_seconds=5), "Visdom server not connected!"
            viz.close(win=None) # close previous plots
            win1 = viz.line( X=np.arange(0, 1), Y=np.arange(0, 1),
                            opts=dict(height=400, width=700, title='Resonator Spectroscopy', showlegend=True, xlabel='expt_pts'))

            for ii in range(py_avg):
                iq_list = prog.acquire(soc, soft_avgs=1, progress=False, remove_offset = False)
                freqs = prog.get_pulse_param("res_pulse", "freq", as_array=True)

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

                viz.line(X = freqs, Y = expt_mags, win=win1, name='I',
                        opts=dict(height=400, width=700, title='Resonator Spectroscopy', showlegend=True, xlabel='expt_pts'))

            amps = np.abs(expt_I + 1j*expt_Q)
            
        else:
            iq_list = prog.acquire(soc, soft_avgs = py_avg, progress=True)
            freqs = prog.get_pulse_param("res_pulse", "freq", as_array=True)
            amps = np.abs(iq_list[0][0].dot([1,1j]))

        print("resonator spectroscopy finished...")
        print(time.time() - start_time, ' s')
        print("===================================")
        time.sleep(10)

        print("Fitting data...")
        ### Fit ###
        fit = Fit()
        # Choose the suitable fitting function
        fit_result = fit.reflection_resonator_spectroscopy(freqs, amps)

        fit_result = {
                "f": fit_result['f'],
                "kc": fit_result['kc'],
                "ki": fit_result['ki'],
                "k": fit_result['k'],
                "offset": fit_result['offset'],
                "slope": fit_result['slope']
            }
    
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
            f.append('fpts', freqs)
            f.append('amps', amps)
            if IS_VISDOM:
                f.append('avgi', expt_I)
                f.append('avgq', expt_Q)
            else:
                f.append('avgi', iq_list[0][0].T[0])
                f.append('avgq', iq_list[0][0].T[1])

            del config['res_freq_ge'] # cant save QickParam <- need to check this for json
            # formats config into file as a single line
            f.attrs['config'] = json.dumps(config)
            f.attrs['fit_result'] = json.dumps(fit_result)

        data = data_path + '\\' + fname

    else: # MUX program
        fpts=[config["start"] + ii*config["step"] for ii in range(config["expts"])]
        fcenter = np.array(config['freqs'])

        avgi = np.zeros((len(fcenter), len(fpts)))
        avgq = np.zeros((len(fcenter), len(fpts)))
        amps = np.zeros((len(fcenter), len(fpts)))
        for index, f in enumerate(tqdm(fpts)):
            config["res_freq_ge"] = fcenter + f
            prog = SingleToneSpectroscopyProgram(soccfg, reps=config["reps"], final_delay=0.5, cfg=config)    
            iq_list = prog.acquire(soc, soft_avgs = config["py_avg"], progress=False)
            for i in range(len(fcenter)):
                avgi[i][index] = iq_list[i][:,0]
                avgq[i][index] = iq_list[i][:,1]
                amps[i][index] = np.abs(iq_list[i][:,0]+1j*iq_list[i][:,1])
        amps = np.array(amps)
        avgi = np.array(avgi)
        avgq = np.array(avgq)

        #####################################
        # ----- Saves data to a file ----- #
        #####################################

        prefix = str(datetime.date.today())
        exp_name = expt_name + '_' + prefix
        print('Experiment name: ' + exp_name)

        fname = get_next_filename(data_path, exp_name, suffix='.h5')
        print('Current data file: ' + fname)

        with SlabFile(data_path + '\\' + fname, 'a') as f:
            # 'a': read/write/create

            # - Adds data to the file - #
            f.append('fpts', fpts)
            f.append('amps', amps)
            f.append('fcenter', fcenter)
            f.append('avgi', avgi)
            f.append('avgq', avgq)

            del config['res_freq_ge'] # dont need to save this...
            # formats config into file as a single line
            f.attrs['config'] = json.dumps(config)

        data = data_path + '\\' + fname

    
    # send to output, data need to be list type
    outputs.set(next={
        "experiment": instructions["experiment"],
        "data": data
    })
    # todo: data can also be saved as a dictionary format