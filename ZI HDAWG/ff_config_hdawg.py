import numpy as np
from matplotlib.pyplot import *

Hw_inv = np.load(r'ff_waveform/comp_kernel.npy')
Hw = np.load(r'ff_waveform/dist_kernel.npy')
# wf_base = np.load(r'ff_waveform/comp_base.npy')

# fasflux_config = {
#     "test":{
#         "amp_factor": 0.1,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#         {"name": "init", "amp": [1.5, -2.5, 0.5, -3.5], "seg": [0, 1000]},
#         {"name": "lattice", "amp": [0, 0, 0, 0], "seg": [1000, 2000]},
#         {"name": "readout", "amp": [1.5, -2.5, 0.5, -3.5], "seg": [2000, 4000]},
#         ],
#         "length": 6000
#     },

#     "iso_q0": {
#         "amp_factor": 0.3,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [0, -1, -1, -1], "seg": [0, 1000]},
#             {"name": "readout", "amp": [0, -1, -1, -1], "seg": [1000, 4000]},
#         ],
#         "length": 5000
#     },
#     "iso_q1": {
#         "amp_factor": 0.3,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [-1, 0, -1, -1], "seg": [0, 1000]},
#             {"name": "readout", "amp": [-1, 0, -1, -1], "seg": [1000, 4000]},
#         ],
#         "length": 5000
#     },
#     "iso_q2": {
#         "amp_factor": 0.3,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [-1, -1, 0, -1], "seg": [0, 1000]},
#             {"name": "readout", "amp": [-1, -1, 0, -1], "seg": [1000, 4000]},
#         ],
#         "length": 5000
#     },
#     "iso_q3": {
#         "amp_factor": 0.3,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [-1, -1, -1, 0], "seg": [0, 1000]},
#             {"name": "readout", "amp": [-1, -1, -1, 0], "seg": [1000, 4000]},
#         ],
#         "length": 5000
#     },
#     "iso_acc_q0": {
#         "amp_factor": 0.3,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [-0.002545, -1, -1, -1], "seg": [0, 1000]},
#             {"name": "readout", "amp": [-0.002545, -1, -1, -1], "seg": [1000, 13000]},
#         ],
#         "length": 15000
#     },
#     "iso_acc_q1": {
#         "amp_factor": 0.3,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [-1, 0.001088, -1, -1], "seg": [0, 1000]},
#             {"name": "readout", "amp": [-1, 0.001088, -1, -1], "seg": [1000, 13000]},
#         ],
#         "length": 15000
#     },
#     "iso_acc_q2": {
#         "amp_factor": 0.3,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [-1, -1, 0.001018, -1], "seg": [0, 1000]},
#             {"name": "readout", "amp": [-1, -1, 0.001018, -1], "seg": [1000, 13000]},
#         ],
#         "length": 15000
#     },
#     "iso_acc_q3": {
#         "amp_factor": 0.3,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [-1, -1, -1, -0.007920], "seg": [0, 1000]},
#             {"name": "readout", "amp": [-1, -1, -1, -0.007920], "seg": [1000, 13000]},
#         ],
#         "length": 15000
#     },
#     "read_q0": {
#         "amp_factor": -0.06,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [2.0, -4, -4, -4], "seg": [0, 1000]},
#             {"name": "readout", "amp": [2.0, -4, -4, -4], "seg": [1000, 6000]},
#         ],
#         "length": 8000
#     },
#     "read_q1": {
#         "amp_factor": -0.06,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [-4, 2, -4, -4], "seg": [0, 1000]},
#             {"name": "readout", "amp": [-4, 2, -4, -4], "seg": [1000, 6000]},
#         ],
#         "length": 8000
#     },
#     "read_q2": {
#         "amp_factor": -0.06,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [-4, -4, 2, -4], "seg": [0, 1000]},
#             {"name": "readout", "amp": [-4, -4, 2, -4], "seg": [1000, 6000]},
#         ],
#         "length": 8000
#     },
#     "read_q3": {
#         "amp_factor": -0.06,  ### multiplex to the amp_array, to adjust the flux amp globally
#         "pulse": [
#             {"name": "init", "amp": [-4, -4, -4, 2], "seg": [0, 1000]},
#             {"name": "readout", "amp": [-4, -4, -4, 2], "seg": [1000, 6000]},
#         ],
#         "length": 8000
#     },
# }

fasflux_config = {
    "test":{
        "amp": 0.4, 
        "length": 5, # length of the pulse in us
    }
}

####################################
## calculate waveforms for HDAWG ###
####################################

def load_wf_hdawg(name = 'test'):
    ff_config = fasflux_config[name]
    ####### calculate waveforms #########
    pulse_info = load_para_from_config(ff_config)
    target_wf = gen_target_wf(pulse_info, ff_config)
    comp_wf = ff_config['amp_factor'] * gen_comp_wf(target_wf, Hw_inv)
    num_flux = len(comp_wf)

    for i in range(num_flux):
        result = [resample_for_hdawg_yonly(comp_wf[i]) for i in range(num_flux)]
        return result

####################################
## waveform calculator help_func ###
####################################
def ff_control_pulse(jump=[[1, 100, 300]], length=6000):
    wf = np.zeros(length)
    for i in range(len(jump)):
        wf[int(jump[i][1]):int(jump[i][2])] = jump[i][0]
    return wf

def load_para_from_config(ff_config):
    ff_para_len = len(ff_config["pulse"])
    n_q = len(ff_config["pulse"][0]["amp"])

    pulse_info = np.zeros((n_q, ff_para_len, 3))

    for i in range(n_q):
        for j in range(ff_para_len):
            pulse_info[i, j] = np.array([ff_config["pulse"][j]["amp"][i]] + ff_config["pulse"][j]["seg"])

    return (pulse_info)

def gen_target_wf(pulse_info, ff_config):
    n_q = len(ff_config["pulse"][0]["amp"])
    target_wf = np.zeros((n_q, ff_config["length"]))

    for i in range(n_q):
        target_wf[i] = ff_control_pulse(pulse_info[i], ff_config["length"])

    return target_wf

def gen_comp_wf(target_wf, Hw_inv):
    num_qubit = Hw_inv.shape[0]
    num_flux = Hw_inv.shape[1]
    kernel_len = Hw_inv.shape[2]

    Hw_matrix_inv = Hw_inv

    wf_len = target_wf.shape[1]
    comp_matrix = np.zeros((num_qubit, num_flux, wf_len))

    prefix = np.zeros(int(kernel_len / 2) - 1)

    for i in range(num_qubit):
        for j in range(num_flux):
            h_inv = np.fft.ifft(Hw_matrix_inv[i, j, :])
            ideal_wf = np.append(prefix, target_wf[j])  ### add zeros to compensate the shift from convolve
            comp_matrix[i][j] = np.convolve(ideal_wf, h_inv, 'same')[:wf_len]

    return np.sum(comp_matrix, axis=1)

def gen_fake_wf(comp_wf, Hw):
    num_qubit = Hw.shape[1]
    num_flux = Hw.shape[0]
    kernel_len = Hw.shape[2]

    Hw_matrix = Hw

    wf_len = comp_wf.shape[1]
    filtered_matrix = np.zeros((num_qubit, num_flux, wf_len))

    prefix = np.zeros(int(kernel_len / 2) - 1)

    for i in range(num_flux):
        for j in range(num_qubit):
            h = np.fft.ifft(Hw_matrix[i, j, :])
            ideal_wf = np.append(prefix, comp_wf[j])  ### add zeros to compensate the shift from convolve
            filtered_matrix[i][j] = np.convolve(ideal_wf, h, 'same')[:wf_len]

    return np.sum(filtered_matrix, axis=1)

def resample_for_hdawg(wf):
    ''' The input wf is sampled at 1GHz, which is the sampleling rate for QM OPX+
    Here we convert it to wavefrom with sampling rate of 2.4GHz for ZI HDAWG
    '''
    y_old = wf
    old_len = len(y_old)
    x_old = np.linspace(1, old_len, old_len)

    new_len = int(2.4 * old_len // 1)
    x_new = np.linspace(1, old_len, new_len)
    y_new = np.interp(x_new, x_old, y_old)

    return y_new, x_new, y_old, x_old

def resample_for_hdawg_yonly(wf):
    ''' The input wf is sampled at 1GHz, which is the sampleling rate for QM OPX+
    Here we convert it to wavefrom with sampling rate of 2.4GHz for ZI HDAWG
    '''
    y_old = wf
    old_len = len(y_old)
    x_old = np.linspace(1, old_len, old_len)

    new_len = int(2.4 * old_len // 1)
    x_new = np.linspace(1, old_len, new_len)
    y_new = np.interp(x_new, x_old, y_old)

    return y_new

####################################
########### testing part ###########
####################################
from malab import *
import matplotlib.pyplot as plt
import json


if __name__ == "__main__":
    ####################################################
    ##### add pulse and waveform into QM config file ###
    ####################################################
    name = 'test'
    ff_config = fasflux_config[name]
    ####### calculate waveforms #########
    pulse_info = load_para_from_config(ff_config)
    target_wf = gen_target_wf(pulse_info, ff_config)
    comp_wf = ff_config['amp_factor']* gen_comp_wf(target_wf, Hw_inv)

    y_new, x_new, y_old, x_old = resample_for_hdawg(comp_wf[0])

    plot(x_old, y_old, '-x')
    plot(x_new, y_new, '-o')




