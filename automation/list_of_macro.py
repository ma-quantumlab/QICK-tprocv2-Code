"""
More on https://docs.quantum-machines.co/0.1/qm-qua-sdk/docs/Guides/best_practices/?h=macro#loops
"""

from qm.qua import *

def measure_ge(ge_ref_st, q_index, cooldown_time):
    """" QUA macro
    prepare and measure g and e state, using this as an reference to normalize the readout data
    ge_ref_st : [Ig,Qg,Ie,Qe] is a list of streams for g,e state readout
    """
    I_g = declare(fixed)  # demodulated and integrated signal for gnd
    Q_g = declare(fixed)  # demodulated and integrated signal for gnd
    I_e = declare(fixed)  # demodulated and integrated signal for exc
    Q_e = declare(fixed)  # demodulated and integrated signal for exc

    # for g state
    align()
    wait(cooldown_time, f'q{q_index}')  # for qubit to decay
    align(f'rr{q_index}', f'q{q_index}')
    measure('readout', f'rr{q_index}', None,
            dual_demod.full('cos', 'out1', 'minus_sin', 'out2', I_g),
            dual_demod.full('sin', 'out1', 'cos', 'out2', Q_g))
    save(I_g, ge_ref_st[0])
    save(Q_g, ge_ref_st[1])

    # for e state
    align()
    wait(cooldown_time, f'q{q_index}')  # for qubit to decay
    play('x180', f'q{q_index}')  # play pi pulse on qubit
    align(f'rr{q_index}', f'q{q_index}')
    measure('readout', f'rr{q_index}', None,
            dual_demod.full('cos', 'out1', 'minus_sin', 'out2', I_e),
            dual_demod.full('sin', 'out1', 'cos', 'out2', Q_e))
    save(I_e, ge_ref_st[2])
    save(Q_e, ge_ref_st[3])

    # extra align in the end
    align()

def measure_gef(I_g_st, Q_g_st, I_e_st, Q_e_st, q_index, cooldown_time):
    """" QUA macro
        prepare and measure g,e and f state, using this as an reference to normalize the readout data
        """