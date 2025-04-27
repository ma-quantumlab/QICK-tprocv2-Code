from malab import *
from malab.datamanagement import SlabFile
from os.path import join
from glob import glob
from malab.dsfit import *
import os 
import datetime
from numpy import *
from tempfile import TemporaryFile

from matplotlib.pyplot import *
from scipy.signal import savgol_filter
import scipy.constants as constants

font = {'weight' : 'normal',
        'size'   : 18}

matplotlib.rc('font', **font)

from malab.instruments.voltsource import *
from malab.instruments.instrumenttypes import *
from malab.instruments.PNAX import N5242A
from malab.dsfit import fithanger_new_withQc
from time import sleep
from copy import *


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

### NWA (PNAX) setup
nwa = N5242A("N5242A", address="192.168.1.44", timeout=10e3) # pnax
print(nwa.get_id())

print('Deviced Connected')

# initial NWA configuration values
num_qubits = int(8)

# read_power = [-60, -65, -60, -60, -60, -60, -55, -55]
read_power = [-50]*num_qubits
read_freq_start = [6.11e9, 6.140e9, 6.16e9, 6.19e9, 6.215e9, 6.235e9, 6.272e9, 6.29e9]
read_freq_stop = [6.136e9, 6.16e9, 6.18e9, 6.215e9, 6.234e9, 6.252e9, 6.282e9, 6.312e9]

# drive_power = [-15, -15, -15, -15, -15, -20, -20, -20] # -40 w 20 attenuation
drive_power = [-15]*num_qubits
drive_freq_start = [3.2e9, 3.2e9, 3.2e9, 3.2e9, 3.2e9, 3.2e9, 3.2e9, 3.2e9]
drive_freq_stop = [5.7e9, 5.7e9, 5.7e9, 5.7e9, 5.7e9, 5.7e9, 5.7e9, 5.7e9]

# single tone
sweep_pts = 1001 #601
ifbw = [2000]*num_qubits
avgs = 3 #10

# two tone
sweep_pts2 = 2001  #1001 #501|
ifbw2 = [1000]*num_qubits
avgs2 = 10

delay = 0

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
# initialize when power to DACs is reset
# dac_C5toC8.initialize()
# dac_D1toD4.initialize()
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
flux_sweep = linspace(-0.1,0.1,11) # in unit not flux quantu, but V w/o correction

# numpts = [41]*num_qubits
# diag_offset = [0.0]*num_qubits
# diag_range = [1e-3]*num_qubits # yoko is in Ampere

# offdiag_range = diag_range
# offdiag_offset = diag_offset


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

TRM = array([[ 1.        , -0.11397061, -0.2587036 , -0.28050569, -0.1660616 ,
        -0.07645482, -0.04368518, -0.00588488],
       [ 0.26125137,  1.        , -0.19756347, -0.33937325, -0.27853692,
        -0.19010634, -0.10639071, -0.016038  ],
       [ 0.22152972,  0.12658328,  1.        , -0.31431047, -0.32633708,
        -0.21942528, -0.14925022, -0.07477466],
       [ 0.21795905,  0.1241314 ,  0.04563477,  1.        , -0.35426775,
        -0.27208706, -0.2074165 , -0.11710245],
       [ 0.24686491,  0.14959481,  0.05232058, -0.06130094,  1.        ,
        -0.36099434, -0.28661645, -0.20891156],
       [ 0.24005248,  0.15270144,  0.06368831, -0.0476997 , -0.13006732,
         1.        , -0.3216176 , -0.26848839],
       [ 0.25187251,  0.163719  ,  0.07630371, -0.02882929, -0.0996814 ,
        -0.17286113,  1.        , -0.37943531],
       [ 0.36707417,  0.2408253 ,  0.11562919, -0.01516484, -0.07545473,
        -0.15037879, -0.23617742,  1.        ]])

# pt = [dc coil, f0, f1, f2, f3, f4, f5, f6, f7]

target = 0 # target flux in mA
qubitInd = 0 # qubit index
pt_target = [0]*9
# pt_target[qubitInd+1] = target
print('flux target =', pt_target)
pt = np.dot(TRM,pt_target[1:])
pt = np.insert(pt, 0, pt_target[0])
print('With crosstalk correction!')
print('flux actual =', pt)
print('\n\n')

# now drive the YOKO and DACs
drive_Yoko_and_DACs(pt)