# from malab.instruments import InstrumentManager
#
# im = InstrumentManager()
# pnax = im['PNAX2']

from malab.instruments import N5242A

pnax = N5242A("N5242A", address="192.168.1.44")
print('Deviced Connected:')
print(pnax.get_id())

# note: switch to cw and then back to pulsed, all pulse parameters remain the same
# still need to restart trigger manually

is_pulsed = 0

if is_pulsed:

    # turning on the pulses
    pnax.write("SENS:PULS0 1")  # automatically sync ADC to pulse gen
    pnax.write("SENS:PULS1 1")
    pnax.write("SENS:PULS2 1")
    pnax.write("SENS:PULS3 1")
    pnax.write("SENS:PULS4 1")
    # turning off the inverting
    pnax.write("SENS:PULS1:INV 0")
    pnax.write("SENS:PULS2:INV 0")
    pnax.write("SENS:PULS3:INV 0")
    pnax.write("SENS:PULS4:INV 0")

else:
    # turning off the pulses
    pnax.write("SENS:PULS0 0")  # automatically sync ADC to pulse gen
    pnax.write("SENS:PULS1 0")
    pnax.write("SENS:PULS2 0")
    pnax.write("SENS:PULS3 0")
    pnax.write("SENS:PULS4 0")
    # turning on the inverting
    pnax.write("SENS:PULS1:INV 1")
    pnax.write("SENS:PULS2:INV 1")
    pnax.write("SENS:PULS3:INV 1")
    pnax.write("SENS:PULS4:INV 1")
