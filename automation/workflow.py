import entropynodes.library as nodes  # noqa: F401
from flame.workflow import Workflow

wf = Workflow("single_qubit_cal", description="res sepc -> qubit spec -> power rabi -> Ramsey -> ...")


# define nodes:
exp_init = nodes.Exp_Init("exp_init")

exp_res_spec = nodes.Exp_Rspec("exp_res_spec")
analysis_res_spec = nodes.Analysis_RSpec("analysis_res_spec")

exp_qubit_spec = nodes.Exp_Qspec("exp_qubit_spec")
analysis_qubit_spec = nodes.Analysis_QSpec("analysis_qubit_spec")

exp_power_rabi = nodes.Exp_Prabi("exp_power_rabi")
analysis_power_rabi = nodes.Analysis_Prabi("analysis_power_rabi")

exp_ramsey = nodes.Exp_Ramsey("exp_ramsey")
analysis_ramsey = nodes.Analysis_Ramsey("analysis_ramsey")

exp_t1 = nodes.Exp_T1("exp_t1")
analysis_t1 = nodes.Analysis_T1("analysis_t1")

# exp_flux = nodes.Exp_Flux_Sweep("exp_flux")

exp_exit = nodes.Exp_Exit("exp_exit")

# in/out of all nodes should contain: exp_config, data
# input to node: "instructions"
# output from node: "previous", "repeat", "next" (exp node only next, analysis node 3 options)

exp_res_spec.i.instructions = exp_init.o.next + analysis_res_spec.o.repeat + analysis_qubit_spec.o.previous #+ exp_flux.o.previous
analysis_res_spec.i.instructions = exp_res_spec.o.next

exp_qubit_spec.i.instructions = analysis_res_spec.o.next + analysis_qubit_spec.o.repeat + analysis_power_rabi.o.previous
analysis_qubit_spec.i.instructions = exp_qubit_spec.o.next

exp_power_rabi.i.instructions = analysis_qubit_spec.o.next + analysis_power_rabi.o.repeat + analysis_ramsey.o.previous
analysis_power_rabi.i.instructions = exp_power_rabi.o.next

exp_ramsey.i.instructions = analysis_power_rabi.o.next + analysis_ramsey.o.repeat + analysis_t1.o.previous
analysis_ramsey.i.instructions = exp_ramsey.o.next

exp_t1.i.instructions = analysis_ramsey.o.next + analysis_t1.o.repeat
analysis_t1.i.instructions = exp_t1.o.next

# exp_flux.i.instructions = analysis_t1.o.next

exp_exit.i.instructions = analysis_t1.o.next# exp_flux.o.next

# end of workflow description

wf.register()
