# The Synthesis and Visualization Tool for Design of Quantum Circuits

The design of quantum circuits is becoming a hot topic of research given that several quantum computers have been built in the last five years 
and some are available for use through APIs. This project targets a quantum circuits design from the software engineering point of view. 
The project combines high level logic optimization algorithms with visualization, parametrization and control interface. 
The implemented synthesis tool allows the user to select desired logic or quantum circuit, specify quantum computer architecture and select parameters
for the synthesis process. In addition a graphic interface allows for a visualization of inputs and outputs.

# Credits

This project is based on the paper by M. Lukac, S. Nursultan, G. Krylov, and O. Kesz ̈ocze, “Geometric
refactoring of quantum and reversible circuits: Quantum layout,” in 2020
23rd Euromicro Conference on Digital System Design (DSD), 2020, pp.
428–435.

# Functionality

When running the program, it checks whether all necessary libraries are installed and asks for a valid IBM 
personal token. It is needed as IBM Q resources are used to run circuits and receive statistics, and it can be obtained 
after registration on the IBM Quantum website. [Link to the IBM Q website](https://quantum-computing.ibm.com/) (Accessed 16 Nov 2022)
![upd_token](https://user-images.githubusercontent.com/39532643/202240062-d4420e19-51d5-45dc-bbf7-8f7b8e6c2206.png)
![upd_connect](https://user-images.githubusercontent.com/39532643/202240084-f1cfbf07-c74f-4923-bcd0-19f1b2eb493d.png)

This is how the application looks after initial launch.
![upd_ui](https://user-images.githubusercontent.com/39532643/202240103-ab97fe57-8472-4078-8c4c-69367241e59e.png)


In the graphical interface the user is able to select several
parameters related to the circuit execution. Those
parameters include: physical architecture which will run a
processed circuit, number of iterations that a circuit will be ran
for, and whether or not a circuit will be ran on a simulator.
The user is able to choose quantum circuits stored in .real
format .

After all parameters where successfully chosen the user will
be able to process the chosen circuit. During this process the
circuit will be reduced to fit the selected IBM Q physical
architecture and the final results will be shown in the GUI’s
output fields. It is important to note that the information about
the circuit’s structure is presented and displayed in terms of
Circuit Interaction Graph (CIG). A CIG is a graph where every
node is a qubit and every edge with its weight represents the
number of interactions between two qubits. Physical nodes
coupling list provided by IBM are used to construct a graph
representing physical circuit. Logical inputs as starting nodes
and incrementally added relations and weights as well as
ancilla bits are used to construct desired logical circuit.

This is how the application window looks after processing a circuit
![upd_ui_full](https://user-images.githubusercontent.com/39532643/202240117-27942016-5602-400a-b3f1-69b49a947d55.png)

# System requirements

All of the program components are written in Python
because the IBM Q API is designed so it can be used in
Python programs extensively. The graphical interface supports
any given operating system and hardware which supports
Python. For the graphical implementation, the visualization
tool relies on third-party GUI library Dear PyGui. For the
algorithm implementation, the tool requires internet connection with IBM Q servers.
