from nodeio.inputs import Inputs
from flame.workflow import Workflow
from flame.utils.identifier import valid_identifier_or_value_error


__all__ = ["Analysis_T1"]


class Analysis_T1(object):

    def __init__(
        self,
        workflow_node_unique_name,
        instructions=None,
    ):
        """finds qubit T1
        
        :param instructions: (dictionary - STREAM) dictionary: {experiment: ..., data:...}
        """
        self._command = "python3"
        self._bin = "node5_analysis_T1.py"
        valid_identifier_or_value_error(workflow_node_unique_name)
        self._name = workflow_node_unique_name
        self._icon = "bootstrap/gear-fill.svg"
        self._inputs = _Inputs(
            self._name, 
            instructions=instructions,
        )
        self._outputs = _Outputs(self._name)
        self._host = {}
        # register the node in the workflow context
        Workflow._register_node(self)

    def host(self, **kwargs):
        """Sets additional options for execution on the host."""
        for key, value in kwargs.items():
            self._host[key] = value
        return self

    @property
    def i(self):
        """Node inputs"""
        return self._inputs

    @property
    def o(self):
        """Node outputs"""
        return self._outputs

    def __str__(self):
        return self._name


class _Inputs(object):

    def __init__(
        self,
        name, 
        instructions=None,
    ):
        self._name = name
        self._inputs = Inputs()

        self._inputs.state("instructions", description="dictionary: {experiment: ..., data:...}", units="dictionary")
        self._inputs.set(instructions=instructions)


    @property
    def instructions(self):
        """Input: dictionary: {experiment: ..., data:...} (dictionary)"""
        return f"#{self._name}/instructions"

    @instructions.setter
    def instructions(self, value):
        """Input: dictionary: {experiment: ..., data:...} (dictionary)"""
        self._inputs.set(instructions=value)
    

class _Outputs(object):

    def __init__(self, name):
        self._name = name
        self._outputs = [
            "next",
            "previous",
            "repeat",
        ]

    @property
    def next(self):
        """Output: dictionary: {experiment: ..., data:...}
        :return: (dictionary)
        """
        return f"#{self._name}/next"

    @property
    def previous(self):
        """Output: dictionary: {experiment: ..., data:...}
        :return: (dictionary)
        """
        return f"#{self._name}/previous"

    @property
    def repeat(self):
        """Output: dictionary: {experiment: ..., data:...}
        :return: (dictionary)
        """
        return f"#{self._name}/repeat"
