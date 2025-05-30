"""
014_Readout_Optimization_ge - optimize readout frequency and gain for g-e transition

This experiment is designed to optimize the readout frequency and gain for the g-e transition.
Here we perform single shot measurements for different readout frequencies and gains by doing a
2D sweep.

MUX and non-MUX versions are setup and work the same for readout. The only difference
is in the data processing. The MUX version uses the QUBIT_INDEX to index the
data, while the non-MUX version does not. TODO: MUX version data processing.

Author: Santi
Date: 2025-05-09
"""

import os
os.chdir(os.getcwd() + '/qick_tprocv2_experiments')

from qick import *
from qick.pyro import make_proxy

from malab import SlabFile, get_next_filename
# for now, all the tProc v2 classes need to be individually imported (can't use qick.*)

# the main program class
from qick.asm_v2 import AveragerProgramV2
# for defining sweeps
from qick.asm_v2 import QickSpan, QickSweep1D

import json
import datetime

# Used for live plotting, need to run "python -m visdom.server" in the terminal and open the IP address in browser
import visdom

from build_task import *
from build_state import *
from qick_setup_funcs import *

from qualang_tools.plot import Fit
import pprint as pp

# import single shot information for g-e calibration
from SingleShot import SingleShotProgram_g, SingleShotProgram_e

# connect to the rfsoc and print soccfg
from rfsoc_connect import *

# ----- Experiment configurations ----- #
expt_name = "Readout_Optimization_ge"
QubitIndex = QUBIT_INDEX
Qubit = 'Q' + str(QubitIndex)

exp_cfg = add_qubit_experiment(expt_cfg, expt_name, QubitIndex)
q_config = all_qubit_state(system_config)
config = {**q_config['Q' + str(QubitIndex)], **exp_cfg}
print(config)

##################
# Define Program #
##################

I_g_array = []
Q_g_array = []
I_e_array = []
Q_e_array = []

for freqs in range(config['freq_steps']):
    I_g_data = []
    Q_g_data = []
    I_e_data = []
    Q_e_data = []
    for gains in range(config['gain_steps']):
        config['res_freq_ge'] = config['freq_start'] + config['freq_step_size']*freqs
        config['res_gain_ge'] = config['gain_start'] + config['gain_step_size']*gains

        ssp_g = SingleShotProgram_g(soccfg, reps=1, final_delay=config['relax_delay'], cfg=config)
        iq_list_g = ssp_g.acquire(soc, soft_avgs=1, progress=False)

        ssp_e = SingleShotProgram_e(soccfg, reps=1, final_delay=config['relax_delay'], cfg=config)
        iq_list_e = ssp_e.acquire(soc, soft_avgs=1, progress=False)

        if MUX == 'False':
            I_g = iq_list_g[0][0].T[0]
            Q_g = iq_list_g[0][0].T[1]
            I_e = iq_list_e[0][0].T[0]
            Q_e = iq_list_e[0][0].T[1]
        else:
            I_g = iq_list_g[QUBIT_INDEX].T[0]
            Q_g = iq_list_g[QUBIT_INDEX].T[1]
            I_e = iq_list_e[QUBIT_INDEX].T[0]
            Q_e = iq_list_e[QUBIT_INDEX].T[1]
    
        I_g_data.append([I_g])
        Q_g_data.append([Q_g])
        I_e_data.append([I_e])
        Q_e_data.append([Q_e])

    I_g_array.append([I_g_data])
    Q_g_array.append([Q_g_data])
    I_e_array.append([I_e_data])
    Q_e_array.append([Q_e_data])


#####################################
# ----- Saves data to a file ----- #
#####################################

prefix = str(datetime.date.today())
exp_name = expt_name + '_Q' + str(QubitIndex) + '_' + prefix
print('Experiment name: ' + exp_name)

data_path = DATA_PATH

fname = get_next_filename(data_path, exp_name, suffix='.h5')
print('Current data file: ' + fname)

with SlabFile(data_path + '\\' + fname, 'a') as f:
    # 'a': read/write/create

    f.append('I_g_array', I_g_array)
    f.append('Q_g_array', Q_g_array)
    f.append('I_e_array', I_e_array)
    f.append('Q_e_array', Q_e_array)
    # f.append('I_f', I_f)
    # f.append('Q_f', Q_f)

    # formats config into file as a single line
    f.attrs['config'] = json.dumps(config)
    
data = data_path + '\\' + fname


