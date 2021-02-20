"""SimpleCTG.py: Implements Circuit Transition Graph"""

__author__ = "Dzhamshed Khaitov"
__email__ = "dzhamshed.khaitov@nu.edu.kz"

import datetime
import os
import heapq
import matplotlib.pyplot as plt
import misc
import sys
from io import StringIO
from copy import deepcopy
from typing import List, Optional, Dict
from qiskit import IBMQ, QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, execute as qiskit_execute
from qiskit.compiler import transpile as qiskit_transpile, assemble as Q_assemble


class SimpleCTG:
    # The gate class to store information of a gate in the circuit.
    class Gate:
        def __init__(self, name: str, variables: List[str]):
            self.name = name
            self.variables = variables

        def __repr__(self):
            return self.name + ' ' + ' '.join(self.variables)

    # machin_name: specify which IBM server to use, if not specified then one with the biggest coupling map is used
    # builtin_funcs: specify whether use qiskit's swap and/or ccx functions by listing them. Ex: ['swap', 'ccx']
    # debugging: to be more verbose and print information on each steps
    def __init__(self, machine_name: Optional[str] = None, builtin_funcs: Optional[List[str]] = None, debugging=False):
        # Quantum machine information
        self.machine_name = machine_name
        self.backend = None
        self.couples = None
        self.qubits_num = 0
        self.connections: Dict[(int, Dict[(int, bool)])] = {}
        self.paths: Dict[(int, Dict[(int, List[int])])] = {}

        # The circuit information
        # The layout is variable -> logical -> physical
        self.circuit: Optional[QuantumCircuit] = None
        # maps variables to physical qubits. Ex: 'a'->0, 'b'->qr[1]
        self._mapping: Dict[(str, int)] = {}
        # maps variables to logical qubits. Ex: 'a'->qr[0], 'b'->qr[1]
        self.variable_to_logical: Dict[(str, int)] = {}
        # reverse of the variable_to_logical
        self.logical_to_variable: Dict[(int, str)] = {}
        # maps logical to physical qubits. Ex: qr[0]->0, qr[1]->1
        self.logical_to_physical: Dict[(int, int)] = {}
        # reverse of the logical_to_physical
        self.physical_to_logical: Dict[(int, str)] = {}

        # The input information
        self.mapping: Dict[(str, int)] = {}
        self.variables_num = 0
        self.variables: List[str] = []
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.constants: Optional[str] = None
        self.garbage: Optional[str] = None
        self.gates: List[SimpleCTG.Gate] = []

        # Helpers
        self.builtin_funcs = builtin_funcs
        self.debugging = debugging
        self.initialized = False

    # Parse the input file.
    # __<name>__ is to hide the function from suggestion in the IDEAs
    def __parse_input__(self, input_file: str):
        if self.debugging:
            print('[INFO] Started parsing file {}'.format(input_file))

        with open(input_file, 'r') as file:
            is_gate = False
            lines = file.readlines()
            file.close()
            for line in lines:
                parts = line.replace('\t', ' ').split(' ')
                variables = list(filter(lambda item: len(item) > 0, [
                                 var.strip() for var in parts[1:]]))
                if line.startswith('.numvars'):
                    self.variables_num = int(parts[1].strip())
                elif line.startswith('.variables'):
                    self.variables = variables
                elif line.startswith('.inputs'):
                    self.inputs = variables
                elif line.startswith('.outputs'):
                    self.outputs = variables
                elif line.startswith('.constants'):
                    self.constants = parts[1].strip()
                elif line.startswith('.garbage'):
                    self.garbage = parts[1].strip()
                elif line.startswith('.begin') or line.startswith('.end'):
                    is_gate = line.startswith('.begin')
                elif is_gate:
                    self.gates.append(SimpleCTG.Gate(
                        parts[0].strip(), variables))

        if self.debugging:
            print('[INFO] Number of variables {}'.format(self.variables_num))
            print('[INFO] Input variables {}'.format(self.inputs))
            print('[INFO] Output variables {}'.format(self.outputs))
            # print('[INFO] GATES:')
            # [print(gate) for gate in self.gates]
            print('[INFO] Finished parsing file {}\n'.format(input_file))

    # Using Dijkstra algorithm find shortest path between vertex and to.
    # This function finds shortest paths between all physical qubits with O(MlogN*N) complexity (M-edges, N-vertices)
    def __shortest_paths__(self):
        for vertex in range(0, self.qubits_num):
            distances = {vertex: 0}
            parent = {}
            queue = []
            heapq.heappush(queue, (0, vertex))
            while len(queue) > 0:
                (d, v) = heapq.heappop(queue)
                if v in distances and distances[v] < d:
                    continue
                for to in self.connections[v].keys():
                    if to not in distances or d + 1 < distances[to]:
                        distances[to] = d + 1
                        heapq.heappush(queue, (d + 1, to))
                        parent[to] = v
            # paths[0][5] = [2, 4, 3] means there's shortest path from 0 to 5 as 0->2->4->3->5
            self.paths[vertex] = {}
            for to in range(0, self.qubits_num):
                if vertex == to or to not in distances:
                    continue
                v = parent[to]
                path = []
                while v != vertex:
                    path.append(v)
                    v = parent[v]
                self.paths[vertex][to] = list(reversed(path))

    # Add a physical qubit as ancilla to the circuit
    def __add_ancilla__(self, physical_qubit: int):
        ancillas_size = sum([1 if key.startswith('ancilla')
                             else 0 for key in self.variable_to_logical])
        variable = 'ancilla' + str(ancillas_size)
        logical = len(self.circuit.qubits)
        self.circuit.add_register(QuantumRegister(1, name=variable))
        self.variable_to_logical[variable] = logical
        self.logical_to_variable[logical] = variable
        self.logical_to_physical[logical] = physical_qubit
        self.physical_to_logical[physical_qubit] = logical
        self._mapping[variable] = physical_qubit

    # Check whether a physical qubit is used as ancilla
    def __is_ancilla_(self, qubit: int):
        return (qubit in self.physical_to_logical
                and self.logical_to_variable[self.physical_to_logical[qubit]].startswith('ancilla'))

    # Returns nearest free ancilla variable
    # If a nearest qubit is not an ancilla then adds it as ancilla
    def __nearest_free_ancilla__(self, variable: str, reserved_qubits: List[str]):
        physical = self.logical_to_physical[self.variable_to_logical[variable]]
        ancilla = -1
        reserved = [self.logical_to_physical[self.variable_to_logical[q]]
                    for q in reserved_qubits]
        for q in range(self.qubits_num):
            if (q not in self.physical_to_logical or (self.__is_ancilla_(q) and q not in reserved)) and (
                    ancilla == -1 or len(self.paths[physical][ancilla]) > len(self.paths[physical][q])):
                ancilla = q
        if ancilla == -1:
            raise Exception('Not enough qubits!')

        if ancilla not in self.physical_to_logical:
            self.__add_ancilla__(ancilla)
        return self.logical_to_variable[self.physical_to_logical[ancilla]]

    # This function moves variables a to b by swapping a through the path to b
    def move_variable(self, a: str, b: str, interchange=False):
        physical_a = self.logical_to_physical[self.variable_to_logical[a]]
        physical_b = self.logical_to_physical[self.variable_to_logical[b]]

        if physical_a == physical_b:
            return

        if physical_a not in self.paths or physical_b not in self.paths[physical_a]:
            raise Exception('No path btw {} (physical {}) and {} (physical {})!!!'.format(
                a, physical_a, b, physical_b))

        for v in self.paths[physical_a][physical_b]:
            # If a physical qubit is not in the initial mapping but it's needed to connect two qubits
            # For example mapping is [(a, 0), (b, 1)] but physical coupling is 0-2-1, we need qubit 2 be in the layout
            if v not in self.physical_to_logical:
                self.__add_ancilla__(v)
            self.swap(a, self.logical_to_variable[self.physical_to_logical[v]])
        if interchange:
            self.swap(a, b)

    # This function swaps two variables using 3 controlled-not gates
    # Variables should be physically connected!
    def swap(self, a: str, b: str):
        if self.circuit is None:
            return
        logical_a = self.variable_to_logical[a]
        logical_b = self.variable_to_logical[b]
        if self.builtin_funcs is not None and 'swap' in self.builtin_funcs:
            return self.circuit.swap(logical_a, logical_b)

        self.circuit.cx(logical_a, logical_b)
        self.circuit.cx(logical_b, logical_a)
        self.circuit.cx(logical_a, logical_b)
        self.variable_to_logical[a] = logical_b
        self.variable_to_logical[b] = logical_a
        self.logical_to_variable[logical_a] = b
        self.logical_to_variable[logical_b] = a

    # This function implements a Controlled-V gate
    def cv(self, control: str, target: str):
        control_position = self.variable_to_logical[control]
        self.move_variable(control, target)
        self.circuit.tdg(self.variable_to_logical[control])
        self.circuit.h(self.variable_to_logical[target])
        self.circuit.cx(
            self.variable_to_logical[target], self.variable_to_logical[control])
        self.circuit.t(self.variable_to_logical[control])
        self.circuit.tdg(self.variable_to_logical[target])
        self.circuit.cx(
            self.variable_to_logical[target], self.variable_to_logical[control])
        self.circuit.h(self.variable_to_logical[target])
        # return to the initial position
        self.move_variable(
            control, self.logical_to_variable[control_position], True)

    # This function implements a Controlled-V+ gate
    def cvdg(self, control: str, target: str):
        control_position = self.variable_to_logical[control]
        self.move_variable(control, target)
        self.circuit.h(self.variable_to_logical[target])
        self.circuit.cx(
            self.variable_to_logical[target], self.variable_to_logical[control])
        self.circuit.t(self.variable_to_logical[target])
        self.circuit.tdg(self.variable_to_logical[control])
        self.circuit.cx(
            self.variable_to_logical[target], self.variable_to_logical[control])
        self.circuit.h(self.variable_to_logical[target])
        self.circuit.t(self.variable_to_logical[control])
        # return to the initial position
        self.move_variable(
            control, self.logical_to_variable[control_position], True)

    # This function implements CCNOT (TOFFOLI) gate
    def ccnot(self, first_control: str, second_control: str, target: str):
        if self.circuit is None:
            return

        if self.builtin_funcs is not None and 'ccx' in self.builtin_funcs:
            return self.circuit.ccx(
                self.variable_to_logical[first_control],
                self.variable_to_logical[second_control],
                self.variable_to_logical[target]
            )

        variable_positions = deepcopy(self.logical_to_variable)

        self.move_variable(second_control, target)
        self.circuit.ch(
            self.variable_to_logical[second_control], self.variable_to_logical[target])
        self.move_variable(first_control, target)
        self.circuit.cz(
            self.variable_to_logical[first_control], self.variable_to_logical[target])
        self.move_variable(second_control, target)
        self.circuit.ch(
            self.variable_to_logical[second_control], self.variable_to_logical[target])

        # return variables to initial positions
        for p, v in variable_positions.items():
            self.move_variable(v, self.logical_to_variable[p], True)

    # This function implements CCNOT (TOFFOLI) gate with 6 NOT gates
    # The Circuit from Wikipedia is used (https://en.wikipedia.org/wiki/Toffoli_gate#Related_logic_gates)
    def ccnot_6_not_gates(self, first_control: str, second_control: str, target: str):
        if self.circuit is None:
            return

        if self.builtin_funcs is not None and 'ccx' in self.builtin_funcs:
            return self.circuit.ccx(
                self.variable_to_logical[first_control],
                self.variable_to_logical[second_control],
                self.variable_to_logical[target]
            )

        # Copy the initial position of all variables for returning them back at initial position after inserting gate
        variable_positions = deepcopy(self.logical_to_variable)

        self.circuit.h(self.variable_to_logical[target])
        self.move_variable(second_control, target)
        self.circuit.cx(
            self.variable_to_logical[second_control], self.variable_to_logical[target])
        self.circuit.tdg(self.variable_to_logical[target])
        self.move_variable(first_control, target)
        self.circuit.cx(
            self.variable_to_logical[first_control], self.variable_to_logical[target])
        self.circuit.t(self.variable_to_logical[target])
        self.move_variable(second_control, target)
        self.circuit.cx(
            self.variable_to_logical[second_control], self.variable_to_logical[target])
        self.circuit.tdg(self.variable_to_logical[target])
        self.move_variable(first_control, target)
        self.circuit.cx(
            self.variable_to_logical[first_control], self.variable_to_logical[target])
        self.circuit.t(self.variable_to_logical[target])
        self.circuit.t(self.variable_to_logical[second_control])
        self.circuit.h(self.variable_to_logical[target])
        self.move_variable(first_control, second_control)
        self.circuit.cx(
            self.variable_to_logical[first_control], self.variable_to_logical[second_control])
        self.circuit.t(self.variable_to_logical[first_control])
        self.circuit.tdg(self.variable_to_logical[second_control])
        self.circuit.cx(
            self.variable_to_logical[first_control], self.variable_to_logical[second_control])

        # return variables to initial positions
        # p is logical position of variable v in ascending order,
        # so it first returns back variable with 0 initial position, after variable with 1 initial position, so on..
        for p, v in variable_positions.items():
            self.move_variable(v, self.logical_to_variable[p], True)

    # This function implements NCCNOT (N-TOFFOLI) gate - a NOT gate with N controlling qubits
    def n_ccnot(self, controllers: List[str], target: str):
        fc = controllers.pop(0)
        sc = controllers.pop(0)
        resets = []
        while len(controllers) > 0:
            # If the ccnot has more than 2 control qubits then wee need insert ancilla qubits
            ancilla = self.__nearest_free_ancilla__(sc, [t[2] for t in resets])
            # Insert ccnot gate
            self.ccnot(fc, sc, ancilla)
            # And save it, because we need to return it back at the end
            resets.append((fc, sc, ancilla))
            fc = ancilla
            sc = controllers.pop(0)
        self.ccnot(fc, sc, target)

        # Reset all of the ancillas to initial state
        # Insert all of the ccnot gate in reverse order, except the last one (all the ccnot gates with ancilla qubits)
        for tpl in reversed(resets):
            self.ccnot(tpl[0], tpl[1], tpl[2])

    # Initialize the IBMQ account and select the backend (quantum machine)
    def initialize(self, hub: Optional[str] = None, group: Optional[str] = None, project: Optional[str] = None):

        # If the machine name defined then get that
        if self.machine_name is not None:
            if self.debugging:
                print('[INFO] Getting the {} information...'.format(
                    self.machine_name))

            self.backend = IBMQ.get_provider(
                hub, group, project).get_backend(self.machine_name)
        # Otherwise search for the quantum machine with the biggest coupling map
        else:
            if self.debugging:
                print('[INFO] Fetching list of backends...')

            backends = IBMQ.get_provider(hub, group, project).backends()

            if self.debugging:
                print(
                    '[INFO] Searching for the backend with the biggest coupling map...')

            # Search for the backend with the biggest coupling map
            for backend in backends:
                coupling_map = backend.configuration().coupling_map

                if coupling_map is not None and (self.couples is None or len(self.couples) < len(coupling_map)):
                    self.backend = backend
                    self.couples = coupling_map

        if self.backend is None:
            raise Exception('No backend was selected')

        configs = self.backend.configuration()
        self.couples = configs.coupling_map
        self.qubits_num = configs.n_qubits

        # Construct a graph where connections[0][1] means physical qubits 0 and 1 are connected
        for couple in self.couples:
            if couple[0] not in self.connections:
                self.connections[couple[0]] = {}
            self.connections[couple[0]][couple[1]] = True

        if self.debugging:
            print('[INFO] selected backend {} with {} qubits'.format(
                configs.backend_name, configs.n_qubits))
            print('[INFO] coupling map is {}\n'.format(self.couples))
            print('[INFO] Finding shortest paths between all qubits')

        # Find shortest path between all of the qubits
        # It's needed for connecting two qubits by swaps
        self.__shortest_paths__()
        self.initialized = True

    # Set the input file (task definition)
    def set_input(self, input_file: str):
        self.gates = []
        self.__parse_input__(input_file)

        if len(self.variables) != len(self.inputs):
            raise Exception(
                'Number of inputs must be same as number of variables')

    # Sets the physical qubits to variables mapping
    # Example: [(a, 0), (b, 1)] means variable a is mapped to physical qubit 0 and variable b to physical qubit 1
    def set_mapping(self, mapping: List[tuple], ancilla_mapping: Optional[List[tuple]] = None):
        if self.debugging:
            print('[INFO] Setting variables to physical mapping...')

        self.mapping = {}
        for t in mapping:
            if t[0] in self.mapping:
                raise Exception(
                    'Variable {} is mapped more than once'.format(t[0]))
            if t[1] in self.mapping.values():
                raise Exception(
                    'Physical qubit {} is mapped to many variables'.format(t[1]))
            if t[1] < 0 or t[1] >= self.qubits_num:
                raise Exception(
                    'Invalid physical qubit index: {}'.format(t[1]))
            self.mapping[t[0]] = t[1]
        if ancilla_mapping:
            for t in ancilla_mapping:
                if not t[0].startswith('ancilla'):
                    raise Exception(
                        'Ancilla variable name must start with "ancilla" (Ex: ancilla0)')
                if t[0] in self.mapping:
                    raise Exception(
                        'Variable {} is mapped more than once'.format(t[0]))
                if t[1] in self.mapping.values():
                    raise Exception(
                        'Physical qubit {} is mapped to many variables'.format(t[1]))
                if t[1] < 0 or t[1] >= self.qubits_num:
                    raise Exception(
                        'Invalid physical qubit index: {}'.format(t[1]))
                self.mapping[t[0]] = t[1]
        if self.debugging:
            print('[INFO] Finished variables to physical mapping')

    # The main function that constructs the circuit
    def construct(self):
        if not self.initialized:
            raise Exception('Initialization is required')

        if len(self.mapping) == 0:
            raise Exception('Variable to physical qubit mapping is required!')

        if len(self.gates) == 0:
            raise Exception(
                'Nothing to construct! Possibly, not input file was provided')

        for variable in self.variables:
            if variable not in self.mapping:
                raise Exception(
                    'Variable {} is not mapped to any physical qubit!'.format(variable))

        if self.debugging:
            print('[INFO] Constructing quantum circuit...')

        self.circuit = QuantumCircuit()
        self._mapping = {}
        self.variable_to_logical = {}
        self.logical_to_variable = {}
        self.logical_to_physical = {}
        self.physical_to_logical = {}
        size = 0
        # Set all of the mappings: variable <-> logical layer <-> physical layer
        for v in self.mapping:
            self._mapping[v] = self.mapping[v]
            self.circuit.add_register(QuantumRegister(1, name=v))
            self.variable_to_logical[v] = size
            self.logical_to_physical[size] = self._mapping[v]
            self.physical_to_logical[self._mapping[v]] = size
            self.logical_to_variable[size] = v
            size += 1

        self.circuit.add_register(ClassicalRegister(len(self.outputs)))

        if self.debugging:
            print('[INFO] Setting constants values...')

        # The size of input is always same as the size of variables
        # Ex: variables: a b c d and input: a 0 c 1 means variables b and d are constants
        for i, v in enumerate(self.inputs):
            if v == '1':
                self.circuit.x(self.variable_to_logical[self.variables[i]])

        for gate in self.gates:
            # if self.debugging:
            #     print('[INFO] Inserting gate: {}'.format(gate))

            if gate.name == 'h' or gate.name == 'H':
                self.circuit.h(self.variable_to_logical[gate.variables[0]])
            elif gate.name == 'T':
                self.circuit.t(self.variable_to_logical[gate.variables[0]])
            elif gate.name == 'T+' or gate.name == 'T*':
                self.circuit.tdg(self.variable_to_logical[gate.variables[0]])
            elif gate.name == 'x' or gate.name == 't1':
                self.circuit.x(self.variable_to_logical[gate.variables[0]])
            elif gate.name.startswith('t') and len(gate.variables) > 2:
                self.n_ccnot(gate.variables[:-1], gate.variables[-1])
            else:
                if gate.name == 'v':
                    self.cv(gate.variables[0], gate.variables[1])
                elif gate.name == 'v+':
                    self.cvdg(gate.variables[0], gate.variables[1])
                elif gate.name == 'cx' or gate.name == 't2':
                    position = self.variable_to_logical[gate.variables[0]]
                    self.move_variable(gate.variables[0], gate.variables[1])
                    control = self.variable_to_logical[gate.variables[0]]
                    target = self.variable_to_logical[gate.variables[1]]
                    self.circuit.cx(control, target)
                    self.move_variable(
                        gate.variables[0], self.logical_to_variable[position], True)
                else:
                    logical_a = self.variable_to_logical[gate.variables[0]]
                    logical_b = self.variable_to_logical[gate.variables[1]]
                    self.move_variable(
                        gate.variables[0], gate.variables[1], True)
                    self.move_variable(
                        gate.variables[1], self.logical_to_variable[logical_a], True)
                    self.variable_to_logical[gate.variables[0]] = logical_a
                    self.variable_to_logical[gate.variables[1]] = logical_b
                    self.logical_to_variable[logical_a] = gate.variables[0]
                    self.logical_to_variable[logical_b] = gate.variables[1]

        if self.debugging:
            print('[INFO] Circuit is constructed!')

    def ibm_layout(self):
        qubits_size = len(self.circuit.qubits)
        return [self.logical_to_physical[q] for q in range(qubits_size)]


# Test a given file
### Simple mapping == True is IBM layout ###
### Simple mapping == False is our layout ###
# def test(ctg: SimpleCTG, input_file: str, output_file: str, simple_mapping=False, debugging=True, limit_100=True,
def test(ctg: SimpleCTG, input_file: str, simple_mapping=False, debugging=True, optimization_level=1, num_of_iterations=None):

    # Create directory outputs/ if it doesn't exist
    os.makedirs('./outputs/txt/', exist_ok=True)
    os.makedirs('./outputs/circuit/', exist_ok=True)

    # make feature keeper
    feature_keeper = {}

    # parse file name
    file_name = input_file.split('/')[-1].split('.')[0]

    # Set the input
    ctg.set_input(input_file)

    # Set variable to physical mapping sequentially, thus a -> 0, b -> 1, c -> 2, etc.
    mapping = [(v, i) for i, v in enumerate(ctg.variables)]
    ancilla_mapping = None
    logical_circuit = None

    if not simple_mapping:
        weighted_graph = misc.Mapping()
        weighted_graph.set_nodes_physical(ctg.couples)
        weighted_graph.physical_add_edges(ctg.couples)
        weighted_graph.construct_ctg(ctg.variables, ctg.gates)
        logical_circuit = list(weighted_graph.logical_graph.edges())
        logical_graph_name, reduced_graph_name = weighted_graph.isomorph(file_name)
        feature_keeper['logical_graph'] = logical_graph_name
        feature_keeper['reduced_graph'] = reduced_graph_name
        mapping, ancilla_mapping = weighted_graph.get_mapping()

    # Set mappings
    ctg.set_mapping(mapping, ancilla_mapping)
    feature_keeper['mapping'] = ctg.mapping
    if debugging:
        print('[INFO] Mapping is', ctg.mapping)

    # Construct the circuit
    ctg.construct()

    # Get the layout as IBM specifies
    layout = ctg.ibm_layout()

    # Get the logical positions of the output variables
    variables_to_measure = [ctg.variable_to_logical[v] for v in ctg.outputs]

    ctg.circuit.measure(variables_to_measure, list(
        range(len(variables_to_measure))))

    # Transpile the circuit https://towardsdatascience.com/what-is-a-quantum-circuit-transpiler-ba9a7853e6f9
    # set the optimization level
    compiled = qiskit_transpile(
        ctg.circuit, ctg.backend, initial_layout=layout, optimization_level=optimization_level)
    assembled = Q_assemble(compiled)
    qasm = compiled.qasm()

    print('[RESULT] cost: {}'.format(
        len(assembled.experiments[0].instructions)))
    # print('[RESULT] qasm:\n{}'.format(qasm))
    if not simple_mapping:
        print('[RESULT] swap: {}'.format(weighted_graph.count_swap(
            ctg.mapping, ctg.paths, logical_circuit)))

    # Use Aer's qasm_simulator
    simulator = Aer.get_backend('qasm_simulator')

    # Execute the circuit on the qasm simulator
    job = qiskit_execute(ctg.circuit, simulator, shots=num_of_iterations)

    # Grab results from the job
    result = job.result()

    # Return counts
    counts = result.get_counts(ctg.circuit)
    print('[RESULT] counts {}'.format(counts))

    # retrieve date
    today = datetime.datetime.today()

    # save qasm to txt file
    qasm_name = './outputs/txt/{}_{}.txt'.format(
        file_name, today.strftime("%Y%m%d%H%M%S"))
    feature_keeper['qasm_file'] = qasm_name

    with open(qasm_name, 'w+') as qasm_file:
        qasm_file.write(qasm)
        qasm_file.close()

    # save circuit image
    try:
        circuit_image_name = './outputs/circuit/{}_{}.txt'.format(
            file_name, today.strftime("%Y%m%d%H%M%S"))
        feature_keeper['ibm_circuit'] = circuit_image_name
        ctg.circuit.draw(filename=circuit_image_name,
                         vertical_compression='high', idle_wires=False, fold=75)
    except Exception as ex:
        feature_keeper['ibm_circuit'] = 'None'
    plt.clf()

    # Create a new circuit with the same amount of quantum and classical registers
    # This is needed to set the initial states of the variables by inserting not gates
    circuit = QuantumCircuit()
    for register in ctg.circuit.qregs:
        circuit.add_register(register)
    for register in ctg.circuit.cregs:
        circuit.add_register(register)

    return feature_keeper


def gui_interaction(circuit_file: str, directory: str, layout_type: bool, optimization_level: int,  architecture: str,
                    num_of_iterations: int):
    """
    Function called by gui.
    """
    # save local copy to put back when done
    stdout = sys.stdout
    # create a special string
    s = StringIO()
    # redirect output
    sys.stdout = s

    # create SimpleCTG instance
    simple_ctg = SimpleCTG(architecture)
    simple_ctg.initialize('ibm-q', 'open', 'main')

    circuit_features = test(simple_ctg, directory + "/" + circuit_file, simple_mapping=layout_type,
                            optimization_level=optimization_level, num_of_iterations=num_of_iterations)

    return s.getvalue(), circuit_features


## MAIN ##
# # try:
# # Set file name
# filename = input("Enter file name without .real: ")

# # Put your IBM token here or set it as None if the credentials are stored on the disk
# TOKEN = 'd3ea16a94139c07aac8b34dc0a5d4d999354b232118788f43abe6c1414ce9b92a89194d5e7488a0fc8bce644b08927e85c4f127cd973cb32e76fc0d1a766758b'
# print('[INFO] Signing in...')
# if TOKEN is not None:
#     IBMQ.enable_account(TOKEN)
# else:
#     IBMQ.load_account()

# simple_ctg = SimpleCTG('ibmq_16_melbourne', debugging=False)
# simple_ctg.initialize('ibm-q', 'open', 'main')

# test(simple_ctg, './tests/' + filename + '.real')
# # except Exception as ex:
# #     print('\n[ERROR] {}'.format(ex))
