# ## Note: I noticed that the code will crash if the two devices are connected to 2 NN USB port on the USB hub,
# ## so I used position '3' and '6' on the USB hub

# from malab.instruments import rfSignalCore

# ## parameter for red sideband LO
# address_red = "1000299D"
# LO_red = int(5.9e9)
# power_red = -25


# ## update the hardware parameters
# print('starting signalcores for red sideband: ' + address_red)
# sc1 = rfSignalCore.SignalCore(name = "SignalCore", address = address_red)
# sc1.set_power(power_red)
# sc1.set_frequency(LO_red)
# sc1.close_device()

# reomote control digital attenuator
import Pyro5.api

power = -20
freq = 5e9
signal_core_01 = Pyro5.api.Proxy("PYRONAME:signal_core_zcu216")    # use name server object lookup uri shortcut

while True:
    try:
        read_power = signal_core_01.set_power(power)
        read_freq = signal_core_01.set_freq(freq)
        break
    except:
        print('Error: signal core not found')

# signal_core_01 = Pyro5.api.Proxy("PYRONAME:signal_core_zcu216")    # use name server object lookup uri shortcut
# read_power = signal_core_01.set_power(power)
# read_freq = signal_core_01.set_freq(freq)

print('Reading freq =', read_freq)
print('Reading power =', read_power)