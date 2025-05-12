Single Qubit Characterization Automation Code

# - Steps to Run the Code - #
0. For the steps below I have used anaconda terminal - this is also where entropy is installed for me
   - To install entropy go to https://entropy-lab.io/0.4/entropylab/getting_started/#start-the-background-service
   - Password: entangle

1. Run Docker on your PC (Install it if you dont have it.)

2. Run "python -m entropyhub --thin-runtime" in your terminal (automation folder containing entropy files)
   - If Docker is not running you will recieve this error message:
     "Docker socket not running. Check Docker Desktop has been started if you use Windows."
   - Leave this terminal open, this ensures entropy remains running in the background during experiments

3. In a new terminal run each of the nodes that will be in the workflow individually. (can skip if nodes are already in entropynodes folder)
   This will help test them as well as create/update the entropynodes folder that contains their information.
   * If you know that the nodes are already up to date then there is no need to dry run
     because it will run the qubit experiments individually, which can be time consuming.

4. Run the app.py code so then in the terminal output of your IDE you will see a link. Click the link and it should bring you to a screen with empty plots.
   - As the workflow script runs in step 5, you will see the plots update with the proper data.

5. Run visdom for fast plotting during each experiment
   - run "python -m visdom.server" in the terminal and open the IP address in browser
   - If you have an error or the connection closes, restart your IDE

6. Next run the workflow script in the terminal by using: "python workflow.py --print-logs". This will run the qubit characterization process with the following experiments:
    1. Resonator Spectroscopy (Experiment <-> Analysis)
    2. Qubit Spectroscopy (Experiment <-> Analysis)
    3. Power Rabi (Experiment <-> Analysis)
    4. Ramsey (T2) (Experiment <-> Analysis)
    5. T1 (Experiment <-> Analysis)

### - Notes - ###

# - Configurations - #
All of the configurations can be viewed/modified in the expt_config.json file.
This file is initially imported to node0_exp_init.py and all of the data is passed between nodes.
The nodes select the designated experiment information contained in the file.
The QubitIndex for all experiments is chosen in node0_exp_init.py after reading in the data file (system_config.json) that contains configurations.

# - Experiments - #
All of the experiments implement the qubit_char_funcs.py file which connects to the zcu216 and
also contains all of the experiment initializations and sequences.

# - Analysis - #
The fitting functions currently used are qulang_tools plotting/fitting functionallity.
   - See "https://github.com/qua-platform/py-qua-tools/tree/main/qualang_tools/plot" for more details 

# - Plotting - #
To view plots in real time (after each analysis) run the app.py script (made by Botao) and view the link output in terminal in your browser.
   - Currently seeing how to do a "live" plot during the experiment.

# - Issues - #


# - Requirements - #
1. nodeio libraries from entropyhub
2. qick libraries
3. Docker application