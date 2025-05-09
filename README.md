MaLab QICK code using tprocV2 firmware
---

Current firmware files being used are located here:
- https://s3df.slac.stanford.edu/people/meeg/qick/tprocv2/2024-09-28_216_tprocv2r21_standard/

Overview
-
The purpose of this code is to run single and multi qubit experiments using RFSoC ZCU-216. Below I will give a brief descrption of what each script does. For more details one should go to each file and look at the description.

*pyro4* is not currenlty used in this code.

*qick_demos_v2* contains a few small examples of how to use tprocv2 (note that some of these are unfinished).

*qick_lib* contains the qick library that the rest of the code uses in the backend.

*qick_tprocv2_experiments* contains the bulk of the code that the user will interact with:
- **Experiment Codes.**
  - *001_time_of_flight.py*: Loopback experiment with time of flight pulse
  - **Single Qubit g-e experiments**:
    - *002_res_spec_ge.py*: Resonator Spectroscopy Experiment for ge state
    - *003_qubit_spec_ge.py*: Qubit Spectroscopy Experiment for ge state
    - *004_time_rabi_ge.py*: Time Rabi Experiment for ge state
    - *005_power_rabi_ge.py*: Power Rabi Experiment for ge state
    - *006_Ramsey_ge.py*: Ramsey Experiment for ge state
    - *007_SpinEcho_ge.py*: Spin Echo Experiment for ge state
    - *008_T1_ge*: T1 Experiment for ge state
  - **Single Qubit e-f experiments**:
    - *009_res_spec_ef.py*: Resonator Spectroscopy Experiment for ef state
    - *010_qubit_spec_ef.py*: Qubit Spectroscopy Experiment for ef state
    - *011_power_rabi_ef.py*: Power Rabi Experiment for ef state
    - *012_Ramsey_ef.py*: Ramsey Experiment for ef state
    - *013_qubit_temp.py*: Measure the temperature of a qubit by performing two length rabi experiments
  - **Readout optimization**:
    - *014_Readout_Optimization_ge.py*: Optimize readout frequency and gain for g-e transition using single shot measurements
    - *014a_Readout_Optimization_gef.py*: Optimize readout frequency and gain for g-e-f transitions using single shot measurements
  - **Experiments Involving DAC and/or YOKO scans**:
    - *015_t1_scan*: Loops over different DAC values and performs T1 measurement for each value
    - *016_mux_t1_scan*: Performs T1 measurement using MUX readout over time
    - *017_res_spec_scan*: Loops over different DAC values and performs resonator spectrosocpy for each value
    - *018_avoided_crossing_expt*: Perform avoided crossing experiment between two qubits
    - *019_collective_decay*: Perform avoided crossing experiment between two qubits and measure T1 time
  - *020_box_mode_sweep*: Perform a ramsey experiment for various LO frequencies and power levels (uses signalCore)
  - *021_qubit_freq_cal*: Quickest way to check resonator and qubit frequencies for a single DAC value
  - **Experiments Involving Zurich Instruments HDAWG**:
    - *022_fast_flux_distortion_expt*: Sweep over qubit pulse timing compared to the fast flux pulse
    - *023_fast_flux_length_sweep_expt*: Sweep over the fast flux pulse length and keep qubit pulse timing fixed compared to the end of the fast flux pulse.
  - **Single Shot Scripts**: Used in all experiments above for performing single shot (can also be used independently)
    - *SingleShot.py*: Perform single shot measurements for g-e calibration
    - *SingleShot_gef.py*: Perform single shot measurements for g-e-f calibration
- **Helper functions used across all experiment scripts.**
  - *build_state.py*: adds the configuration of the pulses and readout to the expt_cfg dictionary
  - *build_task.py*: adds the configuration of the experiment to the expt_cfg dictionary
  - *qick_setup_funcs.py*: contains functions to initialize the experiment configurations and declare channels and pulses
  - *rfsoc_connect.py*: called in each experiment code to connect to the rfsoc and print the configuraitons
- **Misc. helper functions.**
  - *fitting.py*: fitting functions for rabi experiments that are used when the qualang_tools package is not fitting properly. This is a temporary solution until the qualang_tools package is fixed.
  - *qubit_char_funcs.py*: contains the functions for single qubit characterization experiments. This is not implemented yet, but the goal is to call functions from here in more complicated experiments. 

**For data analysis, the current files being used are:** (the data analysis files need to be cleaned up)
- *qubit_char_data_analysis.ipynb*: Contains all single qubit characterization fitting, plotting, and analysis.
- *data_analysis.ipynb*: Contains some of the more complicated experiment data analysis where scans or experiments for multiple qubits are done.


Current Notes / Todos / Bugs
-
- Currently, changing between a constant or Gaussian qubit pulse needs to be done manually by going into the experiment script you are running and setting 'const' to 'gauss' in the pulse parameters.
- All of the e-f experiments have not been updated to include the data processing for MUX readout option (see lines 108-121 and 162-171 of *003_qubit_spec.py* for example)
- The T1 mux scan does not work properly. There is an issues where the readout amplitude for some qubits can be very low or zero. This shows a flat line in the T1 data for a qubit, and is not accurate. This only occurs using MUX readout and only for some qubits. Even when changing the order of the qubit pi pulses, the same issue shows up for the same qubit.
- The experiments all contain a ~0.01 us padding beteween all pulses and readout. This is due to the mismatch between the different clockcycles. Overall, this issue will never be fixed due to the intrinsic difference between the fast_gen channels and the t-processer. However, when using the interpolated channel this is not an issue since the clocks are matched. The padding was added to all experiments just in case, and is especially important when sweeping the lengths of pulses using the fast_gen channels.
- The *qubit_char_funcs.py* file needs to be updated and utilized when wanting to create scans of parameters in more complicated experiments.
- The current experiments using the HDAWG are hardcoded. This instrument needs to be integrated into the configuration files somehow.
- The HDAWG setup is also a work in progress right now. The main focus is inputting custom pulses as a table in the ZI python API.

---

*Author: Santi*

*Date: 2025-05-09*
