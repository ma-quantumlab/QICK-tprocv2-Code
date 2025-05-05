"""
In this experiment I trigger the HDAWG using RFSoC external trigger.
The HDAWG is set to output a square pulse on CH1, and the trigger input is on CH1.
The qubit drive pulse is swept in frequency and timing while the flux and readout pulses are fixed.
"""
import os
os.chdir(os.getcwd() + '/qick_tprocv2_experiments')
print(os.getcwd())
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

# connect to the rfsoc and print soccfg
from rfsoc_connect import *

if SS == 'True':
    # import single shot information for g-e calibration
    from SingleShot import SingleShotProgram_g, SingleShotProgram_e
    from SingleShot import config as ss_config

#importing some functions from toolkit
from zhinst.toolkit import Session, Waveforms, Sequence, CommandTable
from zhinst.toolkit.waveform import Wave, OutputType
import numpy as np
import time


def fast_flux_qubit_spec(q_time, ff_length):
    '''
    Perform qubit spectroscopy, save data, and return qubit frequency found by looking for maximum amplitude.
    '''
    start_time = time.time()
    # ----- Experiment configurations ----- #
    expt_name = "qubit_spec_ge"
    config, expt_name = initialize_configs(expt_name)
    print(expt_name + '\n')
    print(config)
    print(QUBIT_INDEX)
    ##################
    # Define Program #
    ##################

    class PulseProbeSpectroscopyProgram(AveragerProgramV2):
        def _initialize(self, cfg):
            # initialize the readout channels and pulses for DAC and ADC
            initialize_ro_chs(self, cfg, suffix='_ge')

            # add a loop for frequency sweep of qubit pulse frequency
            self.add_loop("freqloop", cfg["steps"])

            # initialize the qubit generator channel
            declare_gen_ch(self, cfg, cfg['qubit_ch'], usage='qubit', suffix='_ge')
            # initialize qubit pulse
            declare_pulse(self, cfg, cfg['qubit_ch'], usage='qubit', 
                        pulse_style='gauss', pulse_name='qubit_pulse', suffix='_ge')

        def _body(self, cfg):
            t_offset = ff_length + 1.5+0.02 # (ro delay, trig delay) time offset for the readout pulse (fixed)

            if q_time < 0:
                # if non-MUX then send readout configurations - useful when freq sweeping
                self.send_readoutconfig(ch=self.cfg['ro_ch'], name="myro", t=0)
                
                self.pulse(ch=self.cfg['res_ch'], name="res_pulse", t=t_offset - q_time)
                self.trigger(ros=[self.cfg['ro_ch']], pins=[0], t=self.cfg['trig_time']+t_offset)

                self.trigger(pins=[1], t=np.abs(q_time))
                self.pulse(ch=self.cfg["qubit_ch"], name="qubit_pulse", t=0.02)
            else:
                # if non-MUX then send readout configurations - useful when freq sweeping
                self.send_readoutconfig(ch=self.cfg['ro_ch'], name="myro", t=0)
                
                self.pulse(ch=self.cfg['res_ch'], name="res_pulse", t=t_offset)
                self.trigger(ros=[self.cfg['ro_ch']], pins=[0], t=self.cfg['trig_time']+t_offset)

                self.trigger(pins=[1], t=0)
                self.pulse(ch=self.cfg["qubit_ch"], name="qubit_pulse", t=0.02 + q_time)

    ###################
    # Run the Program #
    ###################

    qspec=PulseProbeSpectroscopyProgram(soccfg, reps=config['reps'], final_delay=config['relax_delay'], cfg=config)
    py_avg = config['py_avg']

    # for live plotting
    IS_VISDOM = True
    if IS_VISDOM:
        expt_I = expt_Q = expt_mags = expt_phases = expt_pop = None
        viz = visdom.Visdom()
        assert viz.check_connection(timeout_seconds=5), "Visdom server not connected!"
        viz.close(win=None) # close previous plots
        win1 = viz.line( X=np.arange(0, 1), Y=np.arange(0, 1),
            opts=dict(height=400, width=700, title='Qubit Spectroscopy', showlegend=True, xlabel='expt_pts'))

        for ii in range(py_avg):
            iq_list = qspec.acquire(soc, soft_avgs=1, progress=False)
            freqs = qspec.get_pulse_param('qubit_pulse', "freq", as_array=True)

            if MUX == 'False':
                iq_list = iq_list[0][0].T
                # what is the correct shape/index?
                this_I = (iq_list[0])
                this_Q = (iq_list[1])
            else:
                this_I = (iq_list[QUBIT_INDEX].T[0])
                this_Q = (iq_list[QUBIT_INDEX].T[1])

            if expt_I is None: # ii == 0
                expt_I, expt_Q = this_I, this_Q
            else:
                expt_I = (expt_I * ii + this_I) / (ii + 1.0)
                expt_Q = (expt_Q * ii + this_Q) / (ii + 1.0)

            expt_mags = np.abs(expt_I + 1j * expt_Q)  # magnitude
            expt_phases = np.angle(expt_I + 1j * expt_Q)  # phase

            viz.line(X = freqs, Y = expt_mags, win=win1, name='I',
            opts=dict(height=400, width=700, title='Qubit Spectroscopy', showlegend=True, xlabel='expt_pts'))

        amps = np.abs(expt_I + 1j*expt_Q)
        
    else:
        iq_list = qspec.acquire(soc, soft_avgs=py_avg, progress=True)
        freqs = qspec.get_pulse_param('qubit_pulse', "freq", as_array=True)
        amps = np.abs(iq_list[0][0].dot([1,1j]))

    # print(amps.shape)
    if MUX == 'True':
        amps = amps.T[0]
    # # ### Fit ###
    # fit = Fit()
    # # Choose the suitable fitting function
    # fit_result = fit.transmission_resonator_spectroscopy(freqs, amps)

    # # data = fit_result

    # fit_result = {
    #         "f": fit_result['f'],
    #         "kc": fit_result['kc'],
    #         "ki": fit_result['ki'],
    #         "k": fit_result['k'],
    #         "offset": fit_result['offset']
    #     }

    # pp.pprint(fit_result)

    #####################################
    # ----- Saves data to a file ----- #
    #####################################

    prefix = str(datetime.date.today())
    exp_name = expt_name + '_Q' + str(QUBIT_INDEX) + '_' + prefix
    print('Experiment name: ' + exp_name)

    data_path = DATA_PATH

    fname = get_next_filename(data_path, exp_name, suffix='.h5')
    print('Current data file: ' + fname)
    end_time = time.time()
    tot_time = end_time - start_time

    with SlabFile(data_path + '\\' + fname, 'a') as f:
        # 'a': read/write/create
        f.append('expt_time', [int(tot_time)])
        # - Adds data to the file - #
        f.append('fpts', freqs)
        f.append('amps', amps)
        f.append('q_time', [q_time])
        if IS_VISDOM:
            f.append('avgi', expt_I)
            f.append('avgq', expt_Q)
        else:
            f.append('avgi', iq_list[0][0].T[0])
            f.append('avgq', iq_list[0][0].T[1])

        del config['qubit_freq_ge']  # cant save QickParam
        # formats config into file as a single line
        f.attrs['config'] = json.dumps(config) # cant save configs yet with QickParams
        # f.attrs['fit_result'] = json.dumps(fit_result)

    data = data_path + '\\' + fname

    qubit_freq = freqs[np.argmax(amps)]
    return qubit_freq

#################################
### Zurich-Instruments code #####
#################################

'''
This code will play a square pulse with external trigger
The output is on CH1, the trigger input is on CH1

Here the sequence + waveforms are defined in awg_program.code
'''

###############################
### Connecting the device #####
###############################

#defining a connection
device_id='dev9047'

session = Session("127.0.0.1", 8004)  # IP address of rfsoc pc and port of the device
print("devices ready to be connected",session.devices.visible())
device = session.connect_device(device_id)
print("connected to",session.devices.connected())

###################################
#### load HDAWG configurations ####
###################################

# Setting things to default
grouping = 0  # Channel grouping 4X2
device.factory_reset()

def set_awg_default(device=device,
                    grouping=grouping,  # Channel grouping 2x4
                    awg_group=0,  # AWG group
                    output_range=1.0,  # Output range [V]
                    ):
    awg_cores_i = awg_group * 2 ** grouping + np.arange(2 ** grouping)  # AWG cores
    channels_i = awg_group * 2 ** (grouping + 1) + np.arange(2 ** (grouping + 1))  # Output channels

    awg_cores = [device.awgs[awg_core] for awg_core in awg_cores_i]
    channels = [device.sigouts[channel] for channel in channels_i]

    # Per-core settings
    with device.set_transaction():  # This line can be omitted. it
        # "bundles all node set commands into a single transaction.
        # This reduces the network overhead and often increases the speed."

        # Grouping mode
        device.system.awg.channelgrouping(grouping)

        # Per-channel settings
        for channel in channels:
            channel.range(output_range)  # Select the output range
            # channel.on(True)                # Turn on the outputs. Should be the last setting
    return awg_cores_i, channels_i

channels = []
awgs = [0, 1]
for i in awgs:
    awg_cores_i, channels_i = set_awg_default(awg_group=i, output_range=1.0)
    channels.append(channels_i)
print(channels)


###########################
#### program sequencer ####
###########################
# sequencer programming and compilation for sequencer 1

device.awgs[awgs[0]].enable(0)
device.awgs[awgs[1]].enable(0)

awg_program = Sequence()

awg_program.code = """
    const sample_clock = 2.4e9; 
    const sequencer_clock = sample_clock/8;

    const pulse_length = 20e-6; // seconds
    const wait_length = 10e-6; // seconds

    const wait_samples = round(wait_length*sequencer_clock);
    const pulse_samples = round(pulse_length*sample_clock);

    const amp = 0.4; // amplitude of the pulse

    wave w_rect  = amp*rect(pulse_samples, 1);
    
    while (true) {
        waitDigTrigger(1);
        playWave(1, w_rect);
        wait(wait_samples + pulse_samples / 8); // wait for the pulse to finish plus some time (wait_samples)
        playWave(1, -1*w_rect);
      }
    """

device.awgs[awgs[0]].load_sequencer_program(awg_program.code)

###########################
#### Play waveforms ####
###########################
device.sigouts[channels[awgs[0]][0]].on(True)  ### turn the output port ON
device.awgs[awgs[0]].single(True)

time.sleep(.5)
device.awgs[awgs[0]].enable(1) ### run the sequence. ## is this a command in core?

q_times = np.linspace(-1, 10, 100) # in us
ff_length = 20 # fast flux length in us
for q_time in q_times:
    fast_flux_qubit_spec(q_time, ff_length)
    print('q_time = ' + str(q_time) + ' us')

