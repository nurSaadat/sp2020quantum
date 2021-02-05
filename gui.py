#!/usr/bin/env python
"""test.py: Implements graphical user interface"""

__author__ = 'Saadat Nursultan'
__email__ = 'saadat.nursultan@nu.edu.kz'

# installing required libraries first
import os
os.system('pip install -r requirements.txt')

import dearpygui.core as core
import dearpygui.simple as simple
import SimpleCTG 
import time
import traceback
from qiskit import IBMQ

backend_dict = {}
core.add_value('server_on', False)
core.add_value('loading', False)
core.add_value('prev_architecture', 0)
core.add_value('qasmFile', '')

# Callback for menu items
def print_me(sender, data):
        log_debug(f"Menu Item: {sender}")

# fills progress bar
def progressAsync(sender, data):
    counter = 0.0
    while (not core.get_value('server_on')):
        core.set_value('progress', value=counter)
        counter += 0.001
        time.sleep(0.001)
  
# activates IBM account so the backends list can be fetched
def activateIBMAccount():
    TOKEN = 'd3ea16a94139c07aac8b34dc0a5d4d999354b232118788f43abe6c1414ce9b92a89194d5e7488a0fc8bce644b08927e85c4f127cd973cb32e76fc0d1a766758b'
    IBMQ.enable_account(TOKEN) 

# fills the backend_dict
def getBackendsAsync(sender, data):
    activateIBMAccount()
    backends = IBMQ.get_provider().backends()
    # add backend names with indexes, so it will be easier to retrieve them in radio button
    for i in range(len(backends)):
        backend_dict[i] = backends[i].name()
    core.set_value('server_on', True) 
    core.set_value('loading', True)

# displaying all the elements after connecting to IBM
def showButton(sender, data):
    if (core.get_value('server_on')):
        if (core.get_value('loading')):
            core.delete_item('Please wait')
            core.set_value('loading', False)
        core.configure_item('File Selector', show=True)
        core.configure_item('File location:', show=True)
        core.configure_item('##filedir', show=True)
        core.configure_item('File name:', show=True)
        core.configure_item('##file', show=True)
        core.configure_item('Device type:', show=True)
        core.configure_item('radio##1', show=True)
        core.configure_item('Quantum circuit layout method:', show=True)
        core.configure_item('radio##2', show=True)
        core.configure_item('Optimization level:', show=True)
        core.configure_item('##optimization_lvl', show=True)
        core.configure_item('Number of iterations:', show=True)
        core.configure_item('##num_of_iter', show=True)
        core.configure_item('Set Default', show=True)
        core.configure_item('Process', show=True)
        core.configure_item('Input circuit:', show=True)
        core.configure_item('Output circuit:', show=True)
        core.configure_item('Program output:', show=True)
        core.configure_item('Program output will be displayed here', show=True)

# resets all parameters to default
def setDefault(sender, data):
    if core.get_value('device_type') == 0:
        core.add_spacing(name='##space9', count=2)
        core.add_text('Architecture name:', before='##space5')
        core.add_radio_button('radio##3', items=list(backend_dict.values())[1:], source='architecture', before='##space5')
    core.set_value('device_type', 1)
    core.set_value('architecture', 1)
    core.set_value('layout_type', 1)
    core.set_value('opt_level', 1)
    core.set_value('num_of_iter', 100)
    # core.log_debug("Set to default")

# sends the data to SimpleCTG
def process(sender, data):
    directory = core.get_value('directory')
    file_directory = core.get_value('file_directory')
    opt_level = core.get_value('opt_level')
    num_of_iter = core.get_value('num_of_iter')
    
    # converts layout type to boolean for SimpleCTG
    temp = core.get_value('layout_type')
    if temp == 0:
        layout_type = True
    else:
        layout_type = False

    # chooses the device
    if core.get_value('device_type') == 0:
        architecture = backend_dict[0]
    else:
        architecture = backend_dict[core.get_value('architecture') + 1]

    try: 
        infoStr, circuit_features = SimpleCTG.gui_interaction(
            file_directory, directory, layout_type, opt_level, architecture, num_of_iter
            )
        # show program output
        core.configure_item('Program output will be displayed here', color=[255, 255, 255])
        core.draw_image('input_circuit', circuit_features['logical_graph'], [0, 500], pmax=[200,500])
        core.draw_image('output_circuit', circuit_features['reduced_graph'], [0, 500], pmax=[200, 500])
        core.set_value('qasmFile', circuit_features['qasm_file'])
        core.set_value('circuitImage', circuit_features['ibm_circuit'])
        core.set_value('Program output will be displayed here', infoStr)
        core.configure_item('Open qasm file', show=True)
        core.configure_item('Path to IBM circuit representation', show=True)
        core.configure_item('circuitImage', value=core.get_value('circuitImage'))
    except Exception as ex:
        # if error, then makes text red and removes features
        core.configure_item('Program output will be displayed here', color=[255, 0, 0])
        core.set_value('Program output will be displayed here', traceback.format_exc())
        core.clear_drawing('input_circuit')
        core.clear_drawing('output_circuit')
        core.configure_item('Open qasm file', show=False)
        core.configure_item('circuitImage', show=False)
        core.configure_item('Path to IBM circuit representation', show=False)

  
# makes architecture list dynamic
def showArchitectureList(sender, data):
    my_var = core.get_value('device_type')
    if (my_var == 1 and core.get_value('prev_architecture') != 1):
        core.add_spacing(name='##space9', count=2)
        core.add_text('Architecture name:', before='##space5')
        core.add_radio_button('radio##3', items=list(backend_dict.values())[1:], source='architecture', before='##space5')
        core.set_value('prev_architecture', 1)
    elif (my_var == 0 and core.get_value('prev_architecture') != 0):
        core.delete_item('##space9')
        core.delete_item('Architecture name:')
        core.delete_item('radio##3')
        core.set_value('prev_architecture', 0)

# opens file dialog window to choose .pla file
def filePicker(sender, data):
    core.open_file_dialog(callback=applySelectedDirectory, extensions='.real')

# sets the file name 
def applySelectedDirectory(sender, data):
    directory = data[0]
    file_directory = data[1]
    core.set_value('directory', directory)
    core.set_value('file_directory', file_directory)

# Removes the qasm window name 
# TODO: make the function more general
def deleteWindowName(data):
    core.delete_item(data)

# opens window with qasm code
def openQasm(sender, data):
    with simple.window('Qasm code', width=400, height=600, on_close=deleteWindowName('Qasm code')):
        with open(core.get_value('qasmFile'), 'r') as f:
            core.add_text(f.read())

def helpShowArchitectures(sender, data):
    core.configure_item('helpArchitectures', show=True)
    core.configure_item('helpShowInstructions', show=False)

def helpShowInstructions(sender, data):
    core.configure_item('helpShowInstructions', show=True)
    core.configure_item('helpArchitectures', show=False)

def openHelpWindow(sender, data):
    with simple.window('Help##window', width=1000, height=600, on_close=deleteWindowName('Help##window')):
        with simple.menu_bar("Help Menu Bar"):
            core.add_menu_item("Architectures", callback=helpShowArchitectures)
            core.add_menu_item("Instructions", callback=helpShowInstructions)

        with simple.group('helpArchitectures', show="False"):        
            core.add_drawing('armonk', width=72, height=75)
            core.draw_image('armonk', './backends/img/armonk.png', [72, 72])
            core.add_text('ibmq_armonk: 1 qubit.')
            core.add_spacing(name='##space10', count=10)

            core.add_drawing('athens', width=518, height=75)
            core.draw_image('athens', './backends/img/athens-santiago.png', [0, 72])
            core.add_text('ibmq_athens and ibmq_santiago: 5 qubits.')
            core.add_spacing(name='##space10', count=10)

            core.add_drawing('yorktown', width=373, height=400)
            core.draw_image('yorktown', './backends/img/ibmqx2.png', [0, 400])
            core.add_text('ibmqx2: 5 qubits.')
            core.add_spacing(name='##space10', count=10)
            
            core.add_drawing('melb', width=1000, height=196)
            core.draw_image('melb', './backends/img/melbourne.png', [0, 196])
            core.add_text('ibmq_16_melbourne: 15 qubits.')
            core.add_spacing(name='##space10', count=10)

            core.add_drawing('vigo', width=373, height=400)
            core.draw_image('vigo', './backends/img/vigo-ourence-valencia.png', [0, 400])
            core.add_text('ibmq_vigo, ibmq_valencia, and ibmq_ourence: 5 qubits.')
            core.add_spacing(name='##space10', count=10)

        with simple.group('helpInstructions'):
            core.add_text('In the Selector block a user can select optimization parameters:')
            core.add_text('* the level of optimization provided by IBM Q (ranging from 0 to 3)')
            core.add_text('* IBM Original layout or advanced SWAP placement')
            core.add_text('* location of placement')
            core.add_text('* number of iterations.')
            
            instruction_text = """In the Hardware & Circuit block the user can choose between testing the circuit on a quantum computer (IBM Q) and simulator (Qasm). The user also can choose quantum coupling (quantum computer architecture) - from IBM Q or Qasm. Finally, there will be a button to upload an input file.  After selection, the file name will be displayed in the Hardware & Circuit block and the circuit representation will be displayed in the Circuit before the reduction block. When pressing on the Process button the tool will find the optimal mapping of the circuit onto the quantum computer architecture. The resulting mapping will appear in the Circuit after the reduction block."""
            count = 0
            step = 120
            while count < len(instruction_text):
                core.add_text(instruction_text[count: count + step])
                if instruction_text[count + step] != ' ' and instruction_text[count + step] != '-':
                    core.add_same_line()
                    core.add_text('-')
                count += step

def openAboutWindow(sender, data):
    with simple.window('About##window', width=600, height=240, on_close=deleteWindowName('About##window')):
        core.add_text('Developers:') 
        core.add_text('* Valeriy Novossyolov [Computer Science senior student, Nazarbayev University]')
        core.add_text('* Saadat Nursultan [Computer Science senior student, Nazarbayev University]')
        core.add_spacing(name='##space10', count=5)
        core.add_text('Adviser:') 
        core.add_text('* Martin Lukac [Associate Professor, Dep. of Computer Science, Nazarbayev University]')
        core.add_spacing(name='##space10', count=5)
        core.add_text('Developed to support the scientific paper')
        core.add_text("'Geometric Refactoring of Quantum and Reversible Circuits: Quantum Layout'")
        core.add_text('by Martin Lukac, Saadat Nursultan, Georgiy Krylov and Oliver Keszocze')
        

if __name__ == '__main__':
    # Connect to IBM
    core.run_async_function(getBackendsAsync, 0)
    core.set_render_callback(showButton)

    core.set_main_window_size(1500, 900)

    # Progress bar
    with simple.window('Please wait', no_scrollbar=True, height=70, width=400, x_pos=500, y_pos=200):
        core.add_progress_bar('progress', value=0.0, overlay='Connecting to IBM...', width=400)
        core.run_async_function(progressAsync, 0)

    # Title
    core.add_text('Quantum visualization machine ver 1.0.0', color=[52, 73, 235])
    core.add_spacing(name='##space1', count=5)  

    # Menu bar    
    with simple.menu_bar("Main Menu Bar"):

        with simple.menu("File"):

            core.add_menu_item("Save", callback=print_me)
            core.add_menu_item("Save As", callback=print_me)

        core.add_menu_item("Help", callback=openHelpWindow)
        core.add_menu_item("About", callback=openAboutWindow)

    # Parameters group
    with simple.group('left group', width=300):
        # Select file button
        core.add_button('File Selector', callback=filePicker, show=False)
        core.add_spacing(name='##space2', count=3)
        core.add_text('File location:', show=False)
        core.add_label_text('##filedir', value='None Selected', source='directory', show=False)
        core.add_spacing(name='##space3', count=3)
        core.add_text('File name:', show=False)
        core.add_label_text('##file', value='None Selected', source='file_directory', show=False)
        core.add_spacing(name='##space4', count=3)
        # Device type radio button
        core.add_text('Device type:', show=False)
        core.add_radio_button('radio##1', items=['IBM simulator', 'IBM quantum computer'], callback=showArchitectureList, source='device_type', show=False)
        core.add_spacing(name='##space5', count=3)
        # Layout radio button
        core.add_text('Quantum circuit layout method:', show=False)
        core.add_radio_button('radio##2', items=['Original IBM layout', 'Advanced SWAP placement'], source='layout_type', show=False)
        core.add_spacing(name='##space6', count=3)
        # Optimization level slider
        core.add_text('Optimization level:', show=False)
        core.add_slider_int('##optimization_lvl', default_value=1, min_value=0, max_value=3, tip='drag the slider to select an optimization level', width=300, source='opt_level', show=False)
        core.add_spacing(name='##space7', count=3)
        # Number of iterations slider
        core.add_text('Number of iterations:', show=False)
        core.add_slider_int('##num_of_iter', default_value=100, min_value=1, max_value=100, tip='drag the slider to number of iterations', width=300, source='num_of_iter', show=False)
        core.add_spacing(name='##space8', count=3)
        # Default settings button
        core.add_button('Set Default', callback=setDefault, show=False) 
        core.add_spacing(name='##space9', count=3)
        # Process button
        core.add_button('Process', callback=process, show=False)

    # graph images
    core.add_same_line(name='line##3', xoffset=350)
    with simple.group('center group'):       
        # Input circuit preview
        core.add_text('Input circuit:', show=False)
        core.add_drawing('input_circuit', width=600, height=500)
        # Output circuit view
        core.add_text('Output circuit:', show=False)
        core.add_drawing('output_circuit', width=600, height=500)

    # program output
    core.add_same_line(name='line##3', xoffset=1000)
    with simple.group('right group'):
        core.add_button('Open qasm file', callback=openQasm, show=False)
        core.add_text('Path to IBM circuit representation', show=False)
        core.add_label_text('circuitImage')
        core.add_text('Program output:', show=False)
        core.add_text('Program output will be displayed here', show=False, wrap=440)

    opt_level = core.get_value('opt_level')
    num_of_iter = core.get_value('num_of_iter')
    layout_type = core.get_value('layout_type')
    architecture = core.get_value('device_type')
    core.log_debug(layout_type)
    core.log_debug(opt_level)
    core.log_debug(architecture)
    core.log_debug(num_of_iter)

    # core.show_logger()
    core.start_dearpygui()
    