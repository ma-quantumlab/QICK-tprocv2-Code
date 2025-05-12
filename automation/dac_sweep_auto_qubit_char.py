import h5py
from malab import SlabFile, get_next_filename

import json
import datetime
import time

from malab import *
from malab.datamanagement import SlabFile
from numpy import *
import os
import datetime
import os.path
from malab.instruments.PNAX import N5242A
from malab.instruments.voltsource import *
from malab.dsfit import fithanger_new_withQc

import subprocess

#################
# dac functions #
#################

### YOKO setup
YOKO_4 = "192.168.1.77"
YOKO_2 = "192.168.1.57"
YOKO_5 = "192.168.1.141"

dcflux2 = YokogawaGS200(address=YOKO_5) # dc coil
dcflux2.recv_length = 1024
print(dcflux2.recv_length)
print(dcflux2.get_id())
print(dcflux2.get_id())
dcflux2.set_mode('current')
dcflux2.set_range(0.01)  # 10mA range
dcflux2.set_output(True)

# initial NWA configuration values
num_qubits = int(8)

### DACs setup
'''
labelled by flux lines
C5: Q0, C6: Q1, C7: Q2, C8: Q3
D1: Q4, D2: Q5, D3: Q6, D4: D4
'''
dac_C5toC8 = AD5780(address='192.168.1.66')
dac_D1toD4 = AD5780(address='192.168.1.156')
# dacs[qubit index][dac address or channel number]
dacs = [[dac_C5toC8, 1], [dac_C5toC8, 2],[dac_C5toC8, 3],[dac_C5toC8, 4],
        [dac_D1toD4, 1], [dac_D1toD4, 2],[dac_D1toD4, 3],[dac_D1toD4, 4]]

time.sleep(1)

#V/s or mA/s
dac_rate = 0.05

# converts DAC units to current value
def digit_to_curr(x):
    return 20*x/(2**18)-10

# initial offset of DAC channels, measured with volt meter
dac_offset = array([-0.002, -0.004, -0.003, -0.003, -0.004, -0.009, -0.02, -0.024])
diag_offset = dac_offset # set so background is zero, not needed here
#!!!! need to double check units here, w/o crosstalk matrix it should be V


def drive_YOKO(pt):

    print("Driving YOKO at (%.3f) mA" % (pt[0]))
    dcflux2.ramp_current(pt[0]*1e-3, 0.0005) # second argument is rate?
    time.sleep(0.2)

def drive_DACs(pt):

    # I'm leaving this hardcoded for 8 qubits for now - Hebah 2024 12 16
    print("Driving DAC at ( %.3f, %.3f, %.3f, %.3f,%.3f, %.3f, %.3f, %.3f ) mA" %(pt[1], pt[2], pt[3], pt[4], pt[5], pt[6], pt[7], pt[8]))

    for ii in range(len(dacs)):
        print('\n')
        print('Flux line for qubit ', ii)
        print(dacs[ii][0])
        print("Driving DAC at (%.3f) mA" % (pt[ii+1]-dac_offset[ii]))
        dacs[ii][0].get_voltage(dacs[ii][1])
        dacs[ii][0].get_voltage(dacs[ii][1])
        dacs[ii][0].get_voltage(dacs[ii][1])
        dacs[ii][0].get_voltage(dacs[ii][1])
        dac_old = digit_to_curr(int(dacs[ii][0].get_voltage(dacs[ii][1])[:-2]))
        print('old reading = ', dac_old)
        dacs[ii][0].ramp(dacs[ii][1], pt[ii+1], dac_rate)
        time.sleep(1.5 * abs(dac_old - pt[ii+1]) / dac_rate + 5)
        time.sleep(5.0)
        dacs[ii][0].get_voltage(dacs[ii][1])
        dacs[ii][0].get_voltage(dacs[ii][1])
        dacs[ii][0].get_voltage(dacs[ii][1])
        dacs[ii][0].get_voltage(dacs[ii][1])  # to clear the readout queue

def drive_DAC(pt, index):
    ii = index
    print('Driving DAC ' + str(index) + ' at ( %.3f ) mA' %(pt[ii+1]))

    
    print('\n')
    print('Flux line for qubit ', ii)
    print(dacs[ii][0])
    print("Driving DAC at (%.3f) mA" % (pt[ii+1]-dac_offset[ii]))
    dacs[ii][0].get_voltage(dacs[ii][1])
    dacs[ii][0].get_voltage(dacs[ii][1])
    dacs[ii][0].get_voltage(dacs[ii][1])
    dacs[ii][0].get_voltage(dacs[ii][1])
    dac_old = digit_to_curr(int(dacs[ii][0].get_voltage(dacs[ii][1])[:-2]))
    print('old reading = ', dac_old)
    dacs[ii][0].ramp(dacs[ii][1], pt[ii+1], dac_rate)
    time.sleep(1.5 * abs(dac_old - pt[ii+1]) / dac_rate + 5)
    time.sleep(5.0)
    dacs[ii][0].get_voltage(dacs[ii][1])
    dacs[ii][0].get_voltage(dacs[ii][1])
    dacs[ii][0].get_voltage(dacs[ii][1])
    dacs[ii][0].get_voltage(dacs[ii][1])  # to clear the readout queue

def drive_Yoko_and_DACs(pt):
    drive_YOKO(pt)
    drive_DACs(pt)

import flux_values
from flux_values import freqs_q0, corrected_dac_values

flux_array = corrected_dac_values # in unit of mA
flux_array = [arr.tolist() for arr in flux_array]

res_freqs = np.array([6.247] * len(flux_array)) * 1000 # MHz
res_start = res_freqs - [5] * len(res_freqs)
res_stop = res_freqs + [5] * len(res_freqs)

qubit_freqs =  freqs_q0 * 1000 # MHz
qubit_start = qubit_freqs - [10] * len(qubit_freqs)
qubit_stop = qubit_freqs + [20] * len(qubit_freqs)

res_freq_array = []
qubit_freq_array = []
t1_array = []

folder_path_list = []
folder_dict = {}
# print(res_start)
# print(res_stop)

# print(qubit_start)
# print(qubit_stop)

for k, pt in enumerate(flux_array[32:]):
    i = k+32
    start_time = time.time()

    # make a new folder for saving data
    folder_path = 'M:/malab/_Data/20250120 - Santi - RFSoC tprocv2 - LL8qubit T1/data/qubit_0_sweep/' + str(f"{i:05d}")
    # Create the directory
    try:
        os.mkdir(folder_path)
        print(f"Directory '{folder_path}' created successfully.")
    except FileExistsError:
        print(f"Directory '{folder_path}' already exists.")

    folder_path_list.append(folder_path) # save the folder path to a list
    
    # pt = [dc coil, f0, f1, f2, f3, f4, f5, f6, f7]
    # pt_target = [0, target, 0, 0, 0, 0, 0, 0, 0]
    # print('flux target =', pt_target)
    # pt = np.dot(TRM,pt_target[1:])
    # pt = np.insert(pt, 0, pt_target[0])
    print('With crosstalk correction!')
    print('flux actual =', pt)
    print('\n\n')

    # save the flux values for each folder to a dictionary
    folder_dict[folder_path] = {}
    folder_dict[folder_path]['coil'] = pt[0] # save the pt value to a folder dictionary entry
    for j in range(8):
        folder_dict[folder_path]['flux' + str(j)] = pt[j+1]

    # now drive the YOKO and DACs
    drive_Yoko_and_DACs(pt)

    # set up the configurations for the next run
    with open('system_config.json', 'r') as f:
        config = json.load(f)
    
    config['DATA_PATH'] = folder_path # where to save data

    config['config']['dac'] = pt # set the dac values

    qubit_index = config['config']['qubit_index']
    # adjust res_spec experiment configuration values
    config['expt_cfg']['res_spec_ge']['start'][qubit_index] = res_start[i]
    config['expt_cfg']['res_spec_ge']['stop'][qubit_index] = res_stop[i]

    # adjust qubit_spec experiment configuration values
    config['expt_cfg']['qubit_spec_ge']['start'][qubit_index] = qubit_start[i]
    config['expt_cfg']['qubit_spec_ge']['stop'][qubit_index] = qubit_stop[i]

    with open('system_config.json', 'w') as f:
        json.dump(config, f, indent=3)

    # print(os.getcwd())

    file_path = "C:/Users/G41Lab/Dropbox/People/Santi/code/automation/automated_qubit_char tprocV2/automation/workflow.py"

    if os.path.exists(file_path):
        try:
            subprocess.run(["python", file_path, '--print-logs'])
        except RuntimeError or AttributeError:
            print('Error occured during automation.')
            # so we know where the error occurs
            error_file = get_next_filename(folder_path, 'error_file', suffix='.h5')
            print('error file: ' + error_file)
            with SlabFile(folder_path + '\\' + error_file, 'a') as f:
                f.append('error', [1])

    else:
        print(f"Error: File not found: {file_path}")

    # Run the automation command and wait for it to finish
    # subprocess.run(["python workflow.py --print-logs"], capture_output=True, text=True)

    end_time = time.time()

    print('Time taken for iteration =', end_time - start_time)

data_path = 'M:/malab/_Data/20250120 - Santi - RFSoC tprocv2 - LL8qubit T1/data/qubit_0_sweep'
lookup_file = get_next_filename(data_path, 'lookup_file', suffix='.h5')
print('lookup data file: ' + lookup_file)

with SlabFile(data_path + '\\' + lookup_file, 'a') as f:
    # 'a': read/write/create

    # - Adds data to the file - #
    f.create_dataset("folder_names", 
            data=np.array(folder_path_list, dtype=h5py.special_dtype(vlen=str)))
    f.append('dac_list', flux_array)
    f.attrs['folder_dict'] = json.dumps(folder_dict)

drive_Yoko_and_DACs([0] * 9) # zero all the dacs