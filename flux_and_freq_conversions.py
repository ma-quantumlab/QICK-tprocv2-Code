# Created by Hebah 2025 01 27

########## imports ##########

from malab import *
from os.path import join
from glob import glob
from malab.dsfit import *
import os 
from numpy import *
from tempfile import TemporaryFile
#%matplotlib inline
from matplotlib.pyplot import *
from scipy.signal import savgol_filter
import scipy.constants as constants
from qutip import *

font = {'weight' : 'normal',
        'size'   : 18}

matplotlib.rc('font', **font)

from malab.dsfit import fithanger_new_withQc
# some of these are uneccessary but oh well


########## sims ##########

def polynomial(p,x):
    return p[0]+p[1]*(x-p[-1])+p[2]*(x-p[-1])**2+p[3]*(x-p[-1])**3+p[4]*(x-p[-1])**4+p[5]*(x-p[-1])**5+p[6]*(x-p[-1])**6+p[7]*(x-p[-1])**7+p[8]*(x-p[-1])**8+p[9]*(x-p[-1])**9

def fitpolynomial(xdata,ydata,fitparams=None,domain=None,showfit=False,showstartfit=False,label=""):
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata

        fitparams=[0,0,0,0,0,0,0,0,0,0,0,0]

    p1 = fitgeneral(fitdatax,fitdatay,polynomial,fitparams,domain=None,showfit=showfit,showstartfit=showstartfit,label=label)
    return p1

def invertedcos(p,x):
    return p[0]+p[1]/cos(p[2]*x-p[-1])

def fitinvertedcos(xdata,ydata,fitparams=None,domain=None,showfit=False,showstartfit=False,label=""):
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata

        fitparams=[0,0,0,0,0,0,0,0,0,0,0,0]

    p1 = fitgeneral(fitdatax,fitdatay,invertedcos,fitparams,domain=None,showfit=showfit,showstartfit=showstartfit,label=label)
    return p1

# qubit H
def hamiltonian(Ec, Ej, d, flux, N=100):
    """
    Return the charge qubit hamiltonian as a Qobj instance.
    """
    m = np.diag(4 * Ec * (arange(-N,N+1))**2) -  Ej * (cos(pi * flux)*0.5 *(np.diag(np.ones(2*N), -1) + 
                                                               np.diag(np.ones(2*N), 1)) + 
                                                       1j * d * sin(pi * flux)*0.5 *(np.diag(np.ones(2*N), -1) - 
                                                               np.diag(np.ones(2*N), 1)))
    return Qobj(m)

# JC H
def jc_hamiltonian(f_c, f_qs, g, flux, N_r=5, N_q=5):
    
    f_q = Qobj(diag(f_qs[0:N_q]- f_qs[0]))
    a = tensor(destroy(N_r),qeye(N_q))
    b = tensor(qeye(N_r),destroy(N_q))
    H = f_c*a.dag()*a + tensor(qeye(N_r),f_q) + g*(a.dag() + a)*(b.dag()+b)
    return Qobj(H)

def plot_energies(ng_vec, energies, ymax=(20, 3), ymin=(0,0)):
    """
    Plot energy levels as a function of bias parameter ng_vec.
    """
    fig, axes = plt.subplots(1,2, figsize=(16,6))

    for n in range(len(energies[0,:])):
        axes[0].plot(ng_vec, (energies[:,n]-energies[:,0])/(2*pi))
    axes[0].set_ylim(ymin[0], ymax[0])
    axes[0].set_xlabel(r'$flux$', fontsize=18)
    axes[0].set_ylabel(r'$E_n$', fontsize=18)

    for n in range(len(energies[0,:])):
        axes[1].plot(ng_vec, (energies[:,n]-energies[:,0])/(energies[:,1]-energies[:,0]))
    axes[1].set_ylim(ymin[1], ymax[1])
    axes[1].set_xlabel(r'$flux$', fontsize=18)
    axes[1].set_ylabel(r'$(E_n-E_0)/(E_1-E_0)$', fontsize=18)
    return fig, axes

def plot_energies_v2(ng_vec, energies, ymax=(20, 3), ymin=(0,0)):
    """
    Plot energy levels as a function of bias parameter ng_vec.
    """

    for n in range(len(energies[0,:])):
        plt.plot(ng_vec, (energies[:,n]-energies[:,0])/(2*pi),'--',linewidth=1)
    plt.ylim(ymin[0], ymax[0])
    plt.xlabel(r'$flux$', fontsize=20)
    plt.ylabel(r'$E_n$', fontsize=20)


########## params ##########

num_qubits = 8

qubit_order = []
qubit_order.append(range(num_qubits))
qubit_order.append([4, 6, 1, 3, 5, 0, 7, 2])
qubit_order.append([5, 2, 7, 3, 0, 4, 1, 6])


Ec_list = [i*0.001 for i in [212.18, 225.12, 211.18, 215.52, 215.44, 217.56, 217.04, 205.84]]
min_wq_list = [3.65, 3.77, 3.73, 3.68, 3.7, 3.7, 3.65, 3.6]
max_wq_list = [5.335, 5.4, 5.2925, 5.35, 5.3, 5.13, 5.315, 5.3075]

res_freqs = [6.1241,6.1468,6.1674,6.1992,6.223,6.243,6.2709,6.3018]
g_list = [i*0.001 for i in [87, 88, 88, 91, 90, 90, 92, 90]]
dc_flux_periods = [2.65, 3, 2.9, 2.54, 2.7, 2.8, 2.98, 2.7] # mA
# qubit_flux_periods = [28, 21, 37.2, 28.5, 22.5, 39.7, 19, 32.5] # mA
qubit_flux_periods = [28, 21, 37.2, 28.5, 22.5, 28, 19, 32.5] # mA
flux_offsets = [-0.3, -.29, -0.41, -0.32, -0.28, -0.4, -0.26, -0.38] # in terms of flux quanta

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



########## estimate flux ##########

## single qubit
def estimate_flux(freqs, dc_coil, qubit_index, plotting=1):
    dac_values = []

    q_index = qubit_order[2][qubit_index]

    print('Qubit ', qubit_order[1][q_index])
    Ec= 2*pi* Ec_list[q_index] #GHz
    wq_max_guess = max_wq_list[q_index] #GHz
    wq_min_guess = min_wq_list[q_index] #GHz  

    Ej = (2*pi*wq_max_guess+Ec)**2/8/Ec
    d = (wq_min_guess/wq_max_guess)**2

    print('Ec = 2*pi*', Ec/2/pi, ' GHz')
    print('Ej = 2*pi*', Ej/2/pi, ' GHz')
    print('d = ', d)
    print('Ec/Ej = ', Ej/Ec)

    f_c = 2*pi*res_freqs[q_index] #GHz
    g = 2*pi*g_list[q_index] #GHz

    dc_coil_shift = dc_coil/dc_flux_periods[q_index]
    print("DC coil flux offset shift: ", dc_coil_shift)

    flux_vec = np.linspace(-1, 1, 301)

    # qubit energy levels
    # energies = array([hamiltonian(Ec, Ej, d, N, flux+dc_coil_shift).eigenstates()[0] for flux in flux_vec])
    energies = array([hamiltonian(Ec, Ej, d, flux+dc_coil_shift).eigenenergies() for flux in flux_vec])

    # vacuum rabi energy levels
    vr_energies = array([jc_hamiltonian(f_c, energies[ii], g, flux+dc_coil_shift).eigenenergies() for (ii,flux) in enumerate(flux_vec)]) 


    flux_scale= qubit_flux_periods[q_index]
    flux_offset = -flux_scale * flux_offsets[q_index]

    ################################################################################################
    # Find the intersection points

    freq = freqs[qubit_order[1][q_index]]

    intersection_x = []
    # jc_hamiltonian(f_c, energies[ii], g, flux).eigenenergies()
    for i in range(len(flux_vec)-1):
        vr_energies_i = (jc_hamiltonian(f_c, energies[i], g, flux_vec[i]+dc_coil_shift).eigenenergies()[1] - jc_hamiltonian(f_c, energies[i], g, flux_vec[i]+dc_coil_shift).eigenenergies()[0])/(2*pi)
        vr_energies_i_next = (jc_hamiltonian(f_c, energies[i+1], g, flux_vec[i+1]+dc_coil_shift).eigenenergies()[1] - jc_hamiltonian(f_c, energies[i+1], g, flux_vec[i+1]+dc_coil_shift).eigenenergies()[0])/(2*pi)
        if (vr_energies_i - freq) * (vr_energies_i_next - freq) < 0:
            intersection_x.append(flux_vec[i])

    intersection_y = [freq] * len(intersection_x)
    scaled_intersection_x = flux_scale*(array(intersection_x))+flux_offset

    if plotting:
        figure()
        plot(flux_scale*(flux_vec)+flux_offset, (vr_energies[:,1]-vr_energies[:,0])/(2*pi), label='JC curve')
        axhline(freq, label='Freq: '+str(freq), color='r')
        plt.plot(scaled_intersection_x, intersection_y, 'ko', label='Intersection Points')
        xlim(-10,10)
        # title('Qubit '+str(qubit_order[1][q_index]))
        legend(bbox_to_anchor = (1.04,0.5),loc = 'upper left')

    print("Intersection points:", list(zip(scaled_intersection_x, intersection_y)))
    print("Potential flux values: "+str([x for x in scaled_intersection_x if x<10 and x>-10])+" mA")
    dac_values.append([x for x in scaled_intersection_x if x<10 and x>-10])
    print('\n\n')
    print('Array of potetntial DAC values (mA):')
    print(dac_values[0])
    print('\n\n')
    return(dac_values[0])


## all qubits
def estimate_fluxes(freqs, dc_coil, plotting=1):
    dac_values = []
    for q_index in qubit_order[2]:
    
        print('Qubit ', qubit_order[1][q_index])
        Ec= 2*pi* Ec_list[q_index] #GHz
        wq_max_guess = max_wq_list[q_index] #GHz
        wq_min_guess = min_wq_list[q_index] #GHz  

        Ej = (2*pi*wq_max_guess+Ec)**2/8/Ec
        d = (wq_min_guess/wq_max_guess)**2

        print('Ec = 2*pi*', Ec/2/pi, ' GHz')
        print('Ej = 2*pi*', Ej/2/pi, ' GHz')
        print('d = ', d)
        print('Ec/Ej = ', Ej/Ec)

        f_c = 2*pi*res_freqs[q_index] #GHz
        g = 2*pi*g_list[q_index] #GHz

        dc_coil_shift = dc_coil/dc_flux_periods[q_index]
        print("DC coil flux offset shift: ", dc_coil_shift)

        flux_vec = np.linspace(-1, 1, 301)

        # qubit energy levels
        # energies = array([hamiltonian(Ec, Ej, d, N, flux+dc_coil_shift).eigenstates()[0] for flux in flux_vec])
        energies = array([hamiltonian(Ec, Ej, d, flux+dc_coil_shift).eigenenergies() for flux in flux_vec])

        # vacuum rabi energy levels
        vr_energies = array([jc_hamiltonian(f_c, energies[ii], g, flux+dc_coil_shift).eigenenergies() for (ii,flux) in enumerate(flux_vec)]) 


        flux_scale= qubit_flux_periods[q_index]
        flux_offset = -flux_scale * flux_offsets[q_index]

        ################################################################################################
        # Find the intersection points

        freq = freqs[qubit_order[1][q_index]]

        intersection_x = []
        # jc_hamiltonian(f_c, energies[ii], g, flux).eigenenergies()
        for i in range(len(flux_vec)-1):
            vr_energies_i = (jc_hamiltonian(f_c, energies[i], g, flux_vec[i]+dc_coil_shift).eigenenergies()[1] - jc_hamiltonian(f_c, energies[i], g, flux_vec[i]+dc_coil_shift).eigenenergies()[0])/(2*pi)
            vr_energies_i_next = (jc_hamiltonian(f_c, energies[i+1], g, flux_vec[i+1]+dc_coil_shift).eigenenergies()[1] - jc_hamiltonian(f_c, energies[i+1], g, flux_vec[i+1]+dc_coil_shift).eigenenergies()[0])/(2*pi)
            if (vr_energies_i - freq) * (vr_energies_i_next - freq) < 0:
                intersection_x.append(flux_vec[i])

        intersection_y = [freq] * len(intersection_x)
        scaled_intersection_x = flux_scale*(array(intersection_x))+flux_offset

        if plotting:
            figure()
            plot(flux_scale*(flux_vec)+flux_offset, (vr_energies[:,1]-vr_energies[:,0])/(2*pi), label='JC curve')
            axhline(freq, label='Freq: '+str(freq), color='r')
            plt.plot(scaled_intersection_x, intersection_y, 'ko', label='Intersection Points')
            xlim(-10,10)
            # title('Qubit '+str(qubit_order[1][q_index]))
            legend(bbox_to_anchor = (1.04,0.5),loc = 'upper left')

        print("Intersection points:", list(zip(scaled_intersection_x, intersection_y)))
        print("Potential flux values: "+str([x for x in scaled_intersection_x if x<10 and x>-10])+" mA")
        dac_values.append([x for x in scaled_intersection_x if x<10 and x>-10])
        print('\n\n')
    print('Array of potetntial DAC values (mA):')
    print(dac_values)
    print('\n\n')
    return(dac_values)



########## estimate freq ##########

## single qubit
def estimate_freq(pt_array, qubit_index, plotting=1):

    freqs_array = []
    for pt in pt_array:
        q_index = qubit_order[2][qubit_index]
            
        print('Qubit ', qubit_order[1][q_index])
        Ec= 2*pi* Ec_list[q_index] #GHz
        wq_max_guess = max_wq_list[q_index] #GHz
        wq_min_guess = min_wq_list[q_index] #GHz  

        Ej = (2*pi*wq_max_guess+Ec)**2/8/Ec
        d = (wq_min_guess/wq_max_guess)**2

        print('Ec = 2*pi*', Ec/2/pi, ' GHz')
        print('Ej = 2*pi*', Ej/2/pi, ' GHz')
        print('d = ', d)
        print('Ec/Ej = ', Ej/Ec)

        f_c = 2*pi*res_freqs[q_index] #GHz
        g = 2*pi*g_list[q_index] #GHz

        dc_coil_shift = pt[0]/dc_flux_periods[q_index]
        print("DC coil flux offset shift: ", dc_coil_shift)

        flux_vec = np.linspace(-1, 1, 101)

        # qubit energy levels
        # energies = array([hamiltonian(Ec, Ej, d, N, flux+dc_coil_shift).eigenstates()[0] for flux in flux_vec])
        energies = array([hamiltonian(Ec, Ej, d, flux+dc_coil_shift).eigenenergies() for flux in flux_vec])

        # vacuum rabi energy levels
        vr_energies = array([jc_hamiltonian(f_c, energies[ii], g, flux+dc_coil_shift).eigenenergies() for (ii,flux) in enumerate(flux_vec)]) 


        flux_scale= qubit_flux_periods[q_index]
        flux_offset = -flux_scale * flux_offsets[q_index]

        ################################################################################################
        # Find the intersection points


        flux_quanta = ((pt[qubit_order[1][q_index]+1]/qubit_flux_periods[q_index])+flux_offsets[q_index]+dc_coil_shift)
        print(flux_quanta)
        energy = hamiltonian(Ec, Ej, d, flux_quanta).eigenenergies()
        freq =  (jc_hamiltonian(f_c, energy, g, flux_quanta).eigenenergies()[1] - jc_hamiltonian(f_c, energy, g, flux_quanta).eigenenergies()[0])/(2*pi)
        print('Frequency: ', freq)

        if plotting:
            figure()
            plot(flux_scale*(flux_vec)+flux_offset, (vr_energies[:,1]-vr_energies[:,0])/(2*pi), label='JC curve')
            axhline(freq, label='Freq: '+str(freq), color='r')
            plot(pt[qubit_order[1][q_index]+1], freq, 'o', color='r')
            # axvline(pt[qubit_order[1][q_index]+1], color='r')
            xlim(-10,10)
            title('Qubit '+str(qubit_order[1][q_index]))
            legend(bbox_to_anchor = (1.04,0.5),loc = 'upper left')

        
        freqs_array.append(freq)
        print('\n\n')
    print('Array of freqs:')
    print(freqs_array)
    print('\n\n')
    return (freqs_array)


## all qubits
def estimate_freqs(pt_array, plotting=1):

    freqs_array = []
    for pt in pt_array:
        freqs = []
        for q_index in qubit_order[2]:
            
            print('Qubit ', qubit_order[1][q_index])
            Ec= 2*pi* Ec_list[q_index] #GHz
            wq_max_guess = max_wq_list[q_index] #GHz
            wq_min_guess = min_wq_list[q_index] #GHz  

            Ej = (2*pi*wq_max_guess+Ec)**2/8/Ec
            d = (wq_min_guess/wq_max_guess)**2

            print('Ec = 2*pi*', Ec/2/pi, ' GHz')
            print('Ej = 2*pi*', Ej/2/pi, ' GHz')
            print('d = ', d)
            print('Ec/Ej = ', Ej/Ec)

            f_c = 2*pi*res_freqs[q_index] #GHz
            g = 2*pi*g_list[q_index] #GHz

            dc_coil_shift = pt[0]/dc_flux_periods[q_index]
            print("DC coil flux offset shift: ", dc_coil_shift)

            flux_vec = np.linspace(-1, 1, 101)

            # qubit energy levels
            # energies = array([hamiltonian(Ec, Ej, d, N, flux+dc_coil_shift).eigenstates()[0] for flux in flux_vec])
            energies = array([hamiltonian(Ec, Ej, d, flux+dc_coil_shift).eigenenergies() for flux in flux_vec])

            # vacuum rabi energy levels
            vr_energies = array([jc_hamiltonian(f_c, energies[ii], g, flux+dc_coil_shift).eigenenergies() for (ii,flux) in enumerate(flux_vec)]) 


            flux_scale= qubit_flux_periods[q_index]
            flux_offset = -flux_scale * flux_offsets[q_index]

            ################################################################################################
            # Find the intersection point


            flux_quanta = ((pt[qubit_order[1][q_index]+1]/qubit_flux_periods[q_index])+flux_offsets[q_index]+dc_coil_shift)
            print(flux_quanta)
            energy = hamiltonian(Ec, Ej, d, flux_quanta).eigenenergies()
            freq =  (jc_hamiltonian(f_c, energy, g, flux_quanta).eigenenergies()[1] - jc_hamiltonian(f_c, energy, g, flux_quanta).eigenenergies()[0])/(2*pi)
            print('Frequency: ', freq)

            if plotting:
                figure()
                plot(flux_scale*(flux_vec)+flux_offset, (vr_energies[:,1]-vr_energies[:,0])/(2*pi), label='JC curve')
                axhline(freq, label='Freq: '+str(freq), color='r')
                plot(pt[qubit_order[1][q_index]+1], freq, 'o', color='r')
                # axvline(pt[qubit_order[1][q_index]+1], color='r')
                xlim(-10,10)
                title('Qubit '+str(qubit_order[1][q_index]))
                legend(bbox_to_anchor = (1.04,0.5),loc = 'upper left')

            freqs.append(freq)
            print('\n')
        freqs_array.append(freqs)
        print('\n\n')
    print('Array of freqs:')
    print(freqs_array)
    print('\n\n')
    return (freqs_array)