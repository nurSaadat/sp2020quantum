import os
import heapq
from typing import List, Optional, Dict
from qiskit import IBMQ, QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, execute as Q_execute
from qiskit.compiler import transpile as Q_transpile, assemble as Q_assemble

TOKEN = 'a68da99e8beff93e23a7faf4a998b541e0f1eae2b7aa91e68395b1a4bcc026584ff06708430650017cbfde95329e938a01aadb52bed51fa55f22bfe12f4f7fed'


class SimpleCTG:
    # The gate class to store information of a gate in the circuit.
    class Gate:
        def __init__(self, name: str, variables: List[str]):
            self.name = name
            self.variables = variables

        def __repr__(self):
            return self.name + ' ' + ' '.join(self.variables)

    def __init__(self, machine_name: Optional[str] = None, use_builtin_functions=False, debugging=False):
        # Quantum machine information
        self.machine_name = machine_name
        self.backend = None
        self.couples = None
        self.qubits_num = 0
        self.move_variableions: Dict[(int, Dict[(int, bool)])] = {}
        self.paths: Dict[(int, Dict[(int, List[int])])] = {}

        # The circuit information
        # The layout is variable -> logical -> physical
        self.circuit: Optional[QuantumCircuit] = None
        self.mapping: Dict[(str, int)] = {}  # maps variables to physical qubits. Ex: 'a'->0, 'b'->qr[1]
        self.variable_to_logical: Dict[(str, int)] = {}  # maps variables to logical qubits. Ex: 'a'->qr[0], 'b'->qr[1]
        self.logical_to_variable: Dict[(int, str)] = {}  # reverse of the variable_to_logical
        self.logical_to_physical: Dict[(int, int)] = {}  # maps logical to physical qubits. Ex: qr[0]->0, qr[1]->1
        self.physical_to_logical: Dict[(int, str)] = {}  # reverse of the logical_to_physical

        # The input information
        self.initial_mapping: Dict[(str, int)] = {}
        self.variables_num = 0
        self.variables: List[str] = []
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.constants: Optional[str] = None
        self.garbage: Optional[str] = None
        self.gates: List[SimpleCTG.Gate] = []

        # Helpers
        self.use_builtin_functions = use_builtin_functions
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
                variables = list(filter(lambda item: len(item) > 0, [var.strip() for var in parts[1:]]))
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
                    self.gates.append(SimpleCTG.Gate(parts[0].strip(), variables))

        if self.debugging:
            print('[INFO] Number of variables {}'.format(self.variables_num))
            print('[INFO] Input variables {}'.format(self.inputs))
            print('[INFO] Output variables {}'.format(self.outputs))
            print('[INFO] GATES:')
            [print(gate) for gate in self.gates]
            print('[INFO] Finished parsing file {}\n'.format(input_file))

    # Using Dijkstra algorithm find shortest path between vertex and to.
    # This function finds shortest paths between all qubits
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
                for to in self.move_variableions[v].keys():
                    if to not in distances or d + 1 < distances[to]:
                        distances[to] = d + 1
                        heapq.heappush(queue, (d + 1, to))
                        parent[to] = v
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

    def __add_ancilla__(self, physical_qubit: int):
        ancillas_size = sum([1 if key.startswith('ancilla_') else 0 for key in self.variable_to_logical])
        variable = 'ancilla_' + str(ancillas_size)
        logical = len(self.circuit.qubits)
        self.circuit.add_register(QuantumRegister(1, name=variable))
        self.variable_to_logical[variable] = logical
        self.logical_to_variable[logical] = variable
        self.logical_to_physical[logical] = physical_qubit
        self.physical_to_logical[physical_qubit] = logical
        self.mapping[variable] = physical_qubit

    # Check whether a physical qubit is used as ancilla
    def __is_ancilla_(self, qubit: int):
        return (qubit in self.physical_to_logical
                and self.logical_to_variable[self.physical_to_logical[qubit]].startswith('ancilla_'))

    # Returns nearest free ancilla variable
    # If a nearest qubit is not an ancilla then adds it as ancilla
    def __nearest_free_ancilla__(self, variable: str, reserved_qubits: List[str]):
        physical = self.logical_to_physical[self.variable_to_logical[variable]]
        ancilla = -1
        reserved = [self.logical_to_physical[self.variable_to_logical[q]] for q in reserved_qubits]
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
    def move_variable(self, a: str, b: str):
        physical_a = self.logical_to_physical[self.variable_to_logical[a]]
        physical_b = self.logical_to_physical[self.variable_to_logical[b]]
        if physical_a not in self.paths or physical_b not in self.paths[physical_a]:
            raise Exception('No path btw {} (physical {}) and {} (physical {})!!!'.format(a, physical_a, b, physical_b))

        for v in self.paths[physical_a][physical_b]:
            # If a physical qubit is not in the initial mapping but it's needed to connect two qubits
            # For example mapping is [(a, 0), (b, 1)] but physical coupling is 0-2-1, we need qubit 2 be in the layout
            if v not in self.physical_to_logical:
                self.__add_ancilla__(v)
            self.swap(a, self.logical_to_variable[self.physical_to_logical[v]])

    # This function resets qubit a to its initial position
    # This function is called usually after connect function
    def reset_variable(self, variable: str):
        physical = self.logical_to_physical[self.variable_to_logical[variable]]
        initial = self.mapping[variable]

        if physical == initial:
            return

        for v in self.paths[physical][initial]:
            self.swap(variable, self.logical_to_variable[self.physical_to_logical[v]])
        self.swap(variable, self.logical_to_variable[self.physical_to_logical[initial]])

    # This function swaps two qubits
    # Qubits should be physically connected!
    def swap(self, a: str, b: str):
        if self.circuit is None:
            return
        logical_a = self.variable_to_logical[a]
        logical_b = self.variable_to_logical[b]
        if self.use_builtin_functions:
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
        self.move_variable(control, target)
        self.circuit.tdg(self.variable_to_logical[control])
        self.circuit.h(self.variable_to_logical[target])
        self.circuit.cx(self.variable_to_logical[target], self.variable_to_logical[control])
        self.circuit.t(self.variable_to_logical[control])
        self.circuit.tdg(self.variable_to_logical[target])
        self.circuit.cx(self.variable_to_logical[target], self.variable_to_logical[control])
        self.circuit.h(self.variable_to_logical[target])
        self.reset_variable(control)

    # This function implements a Controlled-V+ gate
    def cvdg(self, control: str, target: str):
        self.move_variable(control, target)
        self.circuit.h(self.variable_to_logical[target])
        self.circuit.cx(self.variable_to_logical[target], self.variable_to_logical[control])
        self.circuit.t(self.variable_to_logical[target])
        self.circuit.tdg(self.variable_to_logical[control])
        self.circuit.cx(self.variable_to_logical[target], self.variable_to_logical[control])
        self.circuit.h(self.variable_to_logical[target])
        self.circuit.t(self.variable_to_logical[control])
        self.reset_variable(control)

    # This function implements CCNOT (TOFFOLI) gate
    def ccnot(self, first_control: str, second_control: str, target: str):
        if self.circuit is None:
            return

        if self.use_builtin_functions:
            return self.circuit.ccx(
                self.variable_to_logical[first_control],
                self.variable_to_logical[second_control],
                self.variable_to_logical[target])

        self.move_variable(second_control, target)
        self.circuit.ch(self.variable_to_logical[second_control], self.variable_to_logical[target])
        self.reset_variable(second_control)
        self.move_variable(first_control, target)
        self.circuit.cz(self.variable_to_logical[first_control], self.variable_to_logical[target])
        self.reset_variable(first_control)
        self.move_variable(second_control, target)
        self.circuit.ch(self.variable_to_logical[second_control], self.variable_to_logical[target])
        self.reset_variable(second_control)

    # This function implements CCNOT (TOFFOLI) gate with 6 NOT gates
    # The Circuit from Wikipedia is used (https://en.wikipedia.org/wiki/Toffoli_gate#Related_logic_gates)
    def ccnot_6_not_gates(self, first_control: str, second_control: str, target: str):
        if self.circuit is None:
            return

        if self.use_builtin_functions:
            return self.circuit.ccx(
                self.variable_to_logical[first_control],
                self.variable_to_logical[second_control],
                self.variable_to_logical[target])

        self.circuit.h(self.variable_to_logical[target])
        self.move_variable(second_control, target)
        self.circuit.cx(self.variable_to_logical[second_control], self.variable_to_logical[target])
        self.reset_variable(second_control)
        self.circuit.tdg(self.variable_to_logical[target])
        self.move_variable(first_control, target)
        self.circuit.cx(self.variable_to_logical[first_control], self.variable_to_logical[target])
        self.reset_variable(first_control)
        self.circuit.t(self.variable_to_logical[target])
        self.move_variable(second_control, target)
        self.circuit.cx(self.variable_to_logical[second_control], self.variable_to_logical[target])
        self.reset_variable(second_control)
        self.circuit.tdg(self.variable_to_logical[target])
        self.move_variable(first_control, target)
        self.circuit.cx(self.variable_to_logical[first_control], self.variable_to_logical[target])
        self.reset_variable(first_control)
        self.circuit.t(self.variable_to_logical[target])
        self.circuit.t(self.variable_to_logical[second_control])
        self.circuit.h(self.variable_to_logical[target])
        self.move_variable(first_control, second_control)
        self.circuit.cx(self.variable_to_logical[first_control], self.variable_to_logical[second_control])
        self.circuit.t(self.variable_to_logical[first_control])
        self.circuit.tdg(self.variable_to_logical[second_control])
        self.circuit.cx(self.variable_to_logical[first_control], self.variable_to_logical[second_control])
        self.reset_variable(first_control)

    # This function implements NCCNOT (N-TOFFOLI) gate - a NOT gate with N controlling qubits
    def n_ccnot(self, controllers: List[str], target: str):
        fc = controllers.pop(0)
        sc = controllers.pop(0)
        resets = []
        while len(controllers) > 0:
            ancilla = self.__nearest_free_ancilla__(sc, [t[2] for t in resets])
            self.ccnot(fc, sc, ancilla)
            resets.append((fc, sc, ancilla))
            fc = ancilla
            sc = controllers.pop(0)
        self.ccnot(fc, sc, target)
        # Reset all of the ancillas to initial state
        for tpl in reversed(resets):
            self.ccnot(tpl[0], tpl[1], tpl[2])

    # Initialize the IBMQ account and select the backend (quantum machine)
    def initialize(self, hub: Optional[str] = None, group: Optional[str] = None, project: Optional[str] = None):

        if self.machine_name is not None:
            if self.debugging:
                print('[INFO] Getting the {} information...'.format(self.machine_name))

            self.backend = IBMQ.get_provider(hub, group, project).get_backend(self.machine_name)

        else:
            if self.debugging:
                print('[INFO] Fetching list of backends...')

            backends = IBMQ.get_provider(hub, group, project).backends()

            if self.debugging:
                print('[INFO] Searching for the backend with the most coupling map...')

            # Search for the backend with the most coupling map
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

        for couple in self.couples:
            if couple[0] not in self.move_variableions:
                self.move_variableions[couple[0]] = {}
            self.move_variableions[couple[0]][couple[1]] = True

        if self.debugging:
            print('[INFO] selected backend {} with {} qubits'.format(configs.backend_name, configs.n_qubits))
            print('[INFO] coupling map is {}\n'.format(self.couples))
            print('[INFO] Finding shortest paths between all qubits')

        self.__shortest_paths__()
        self.initialized = True

    # Set the input file (task definition)
    def set_input(self, input_file: str):
        self.gates = []
        self.__parse_input__(input_file)

    # Sets the physical qubits to variables mapping
    # Example: [(a, 0), (b, 1)] means variable a is mapped to physical qubit 0 and variable b to physical qubit 1
    def set_mapping(self, mapping: List[tuple], ancilla_mapping: Optional[List[tuple]] = None):
        if self.debugging:
            print('[INFO] Setting variables to physical mapping...')

        self.initial_mapping = {}
        for t in mapping:
            if t[0] in self.initial_mapping:
                raise Exception('Variable {} is mapped more than once'.format(t[0]))
            if t[1] in self.initial_mapping.values():
                raise Exception('Physical qubit {} is mapped to many variables'.format(t[1]))
            if t[1] < 0 or t[1] >= self.qubits_num:
                raise Exception('Invalid physical qubit index: {}'.format(t[1]))
            self.initial_mapping[t[0]] = t[1]
        if ancilla_mapping:
            for t in ancilla_mapping:
                if t[0].startswith('ancilla_'):
                    raise Exception('Ancilla variable name must start with "ancilla_" (Ex: ancilla_0)')
                if t[0] in self.initial_mapping:
                    raise Exception('Variable {} is mapped more than once'.format(t[0]))
                if t[1] in self.initial_mapping.values():
                    raise Exception('Physical qubit {} is mapped to many variables'.format(t[1]))
                if t[1] < 0 or t[1] >= self.qubits_num:
                    raise Exception('Invalid physical qubit index: {}'.format(t[1]))
                self.initial_mapping[t[0]] = t[1]
        if self.debugging:
            print('[INFO] Finished variables to physical mapping')

    # The main function
    def construct(self):
        if not self.initialized:
            raise Exception('Initialization is required')

        if len(self.initial_mapping) == 0:
            raise Exception('Variable to physical qubit mapping is required!')

        if len(self.gates) == 0:
            raise Exception('Nothing to construct! Possibly, not input file was provided')

        for variable in self.variables:
            if variable not in self.initial_mapping:
                raise Exception('Variable {} is not mapped to any physical qubit!'.format(variable))
            self.mapping[variable] = self.initial_mapping[variable]

        if self.debugging:
            print('[INFO] Constructing quantum circuit...')

        self.circuit = QuantumCircuit()
        self.mapping = {}
        self.variable_to_logical = {}
        self.logical_to_variable = {}
        self.logical_to_physical = {}
        self.physical_to_logical = {}
        size = 0
        for v in self.initial_mapping:
            self.mapping[v] = self.initial_mapping[v]
            self.circuit.add_register(QuantumRegister(1, name=v))
            self.variable_to_logical[v] = size
            self.logical_to_physical[size] = self.mapping[v]
            self.physical_to_logical[self.mapping[v]] = size
            self.logical_to_variable[size] = v
            size += 1

        self.circuit.add_register(ClassicalRegister(len(self.outputs)))

        if self.debugging:
            print('[INFO] Setting constants values...')

        for i, v in enumerate(self.inputs):
            if v == '1':
                self.circuit.x(self.variable_to_logical[self.variables[i]])

        for gate in self.gates:
            if self.debugging:
                print('[INFO] Inserting gate: {}'.format(gate))

            if gate.name == 'h':
                self.circuit.h(self.variable_to_logical[gate.variables[0]])
            elif gate.name == 'x' or gate.name == 't1':
                self.circuit.x(self.variable_to_logical[gate.variables[0]])
            elif gate.name.startswith('t') and len(gate.variables) > 2:
                self.n_ccnot(gate.variables[:-1], gate.variables[-1])
            else:
                if gate.name == 'cx' or gate.name == 't2':
                    self.move_variable(gate.variables[0], gate.variables[1])
                    control = self.variable_to_logical[gate.variables[0]]
                    target = self.variable_to_logical[gate.variables[1]]
                    self.circuit.cx(control, target)
                    self.reset_variable(gate.variables[0])
                elif gate.name == 'v':
                    self.cv(gate.variables[0], gate.variables[1])
                elif gate.name == 'v+':
                    self.cvdg(gate.variables[0], gate.variables[1])
                else:
                    self.move_variable(gate.variables[0], gate.variables[1])
                    self.swap(gate.variables[0], gate.variables[1])
                    self.reset_variable(gate.variables[0])

        if self.debugging:
            print('[INFO] Circuit is constructed!')

    def ibm_layout(self):
        qubits_size = len(self.circuit.qubits)
        return [self.logical_to_physical[q] for q in range(qubits_size)]


def test(ctg: SimpleCTG, input_file: str, output_file: str, simple_mapping=True, debugging=True, limit_100=True,
         draw_circuit=False):
    os.makedirs('./outputs/simple_ctg/', exist_ok=True)

    ctg.set_input(input_file)

    if simple_mapping:
        ctg.set_mapping([(v, i) for i, v in enumerate(ctg.variables)])

    ctg.construct()
    ibm_layout = ctg.ibm_layout()

    variables_to_measure = [ctg.variable_to_logical[v] for v in ctg.outputs]

    ctg.circuit.measure(variables_to_measure, list(range(len(variables_to_measure))))
    compiled = Q_transpile(ctg.circuit, ctg.backend, initial_layout=ibm_layout)
    # assembled = Q_assemble(compiled)
    qasm = compiled.qasm()
    # if debugging:
    #     print('[RESULT] cost: {}'.format(len(assembled.experiments[0].instructions)))
    #     print('[RESULT] qasm:\n{}\n'.format(qasm))

    file_name = input_file.split('/')[-1].split('.')[0]
    with open('./outputs/simple_ctg/{}.txt'.format(file_name), 'w+') as qasm_file:
        qasm_file.write(qasm)
        qasm_file.close()

    if draw_circuit:
        if debugging:
            print('[INFO] Drawing the circuit....')
        ctg.circuit.draw(filename='./outputs/simple_ctg/{}.png'.format(file_name), output='mpl')

    simulator = Aer.get_backend('qasm_simulator')
    circuit = QuantumCircuit()
    for register in ctg.circuit.qregs:
        circuit.add_register(register)
    for register in ctg.circuit.cregs:
        circuit.add_register(register)

    # Testing
    with open(output_file, 'r') as test_file:
        lines = test_file.readlines()
        test_file.close()
        for index, line in enumerate(lines):
            if not line.startswith('.') and not line.startswith('#'):
                if limit_100 and index > 100:
                    print('[WARNING] TOO MANY INPUTS! Aborting....')
                    return
                parts = line.replace('\t', ' ').split(' ')
                inputs = list(parts[0].strip())
                output = parts[1].strip()

                test_circuit = circuit.copy()
                for v in ctg.inputs:
                    if v != '0' and v != '1' and len(inputs) > 0 and inputs.pop(0) == '1':
                        test_circuit.x(ctg.variable_to_logical[v])
                test_circuit.extend(ctg.circuit)

                test_circuit.measure(variables_to_measure, list(range(len(variables_to_measure))))
                job = Q_execute(test_circuit, simulator)
                result = list(job.result().get_counts()).pop().strip()[::-1]

                if debugging:
                    print('[INFO] Test number {}: {} | {}'.format(index, result, output), end='\r')
                if result != output:
                    raise Exception('WA for {}: expected {}, found {}'.format(parts[0].strip(), output, result))


def test_all(ctg: SimpleCTG):
    # parity task has 16 qubits and it has wrong inputs in the parity.pla
    # testCV is incorrect
    exclude = ["parity", "testCV"]

    test_files = os.listdir('./tests/')

    for file_name in test_files:
        if file_name.endswith('.real') and file_name.split('.')[0] + '.pla' in test_files and file_name not in exclude:
            print('-------------------- {} --------------------'.format(file_name))
            try:
                test(ctg, './tests/' + file_name, './tests/{}.pla'.format(file_name.split('.')[0]))
            except Exception as e:
                print('[ERROR] {}'.format(e))
            print('\n')


try:
    print('[INFO] Signing in...')
    IBMQ.enable_account(TOKEN)
    simple_ctg = SimpleCTG('ibmq_16_melbourne', debugging=True)
    simple_ctg.initialize('ibm-q', 'open', 'main')
    # test_all(simple_ctg)
    test(simple_ctg, './tests/toffoli.real', './tests/toffoli.pla', limit_100=False)
except Exception as e:
    print('[ERROR] {}'.format(e))
