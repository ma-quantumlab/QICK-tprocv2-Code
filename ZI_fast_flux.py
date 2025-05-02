'''
This code will play a square pulse with external trigger
The output is on CH1, the trigger input is on CH1

Here the sequence + waveforms are defined in awg_program.code
'''

###############################
### Connecting the device #####
###############################

#importing some functions from toolkit
from zhinst.toolkit import Session, Waveforms, Sequence, CommandTable
from zhinst.toolkit.waveform import Wave, OutputType
import numpy as np
import time

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

# awg_program.constants['N'] = 500
# awg_program.constants['amp'] = 10

awg_program.code = """
    const sample_clock = 2.4e9; 
    const sequencer_clock = sample_clock/8;

    const pulse_length = 20e-6; // seconds
    const wait_length = 10e-6; // seconds

    const wait_samples = round(wait_length*sequencer_clock);
    const pulse_samples = round(pulse_length*sample_clock/16)*16;

    const N = pulse_samples;
    const amp = 1;

    wave w_rect  = 0.2*rect(N, amp);
    
    while (true) {
        waitDigTrigger(1);
        playWave(1, w_rect);
        wait(wait_samples);
        playWave(1, -1*w_rect);
      }
    """
# awg_program.code = """
#     const N = 6000;
#     const amp = 1;

#     wave w_rect  = 0.5*rect(N, amp);
    
#     var j;
#     for (j = 0; j < 100; j = j + 1) {
#         waitDigTrigger(1);
#         playWave(1, w_rect);
#       }
#     """
device.awgs[awgs[0]].load_sequencer_program(awg_program.code)

###########################
#### Play waveforms ####
###########################
device.sigouts[channels[awgs[0]][0]].on(True)  ### turn the output port ON
device.awgs[awgs[0]].single(True)

time.sleep(.5)
device.awgs[awgs[0]].enable(1) ### run the sequence. ## is this a command in core?