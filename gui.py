#!/usr/bin/env python

"""test.py: Implements graphical user interface"""

__author__ = 'Saadat Nursultan'
__email__ = 'saadat.nursultan@nu.edu.kz'

# installing required libraries first
import os
os.system('pip install -r requirements.txt')


import dearpygui.core as core
import dearpygui.simple as simple
import time
import traceback
from qiskit import IBMQ
import SimpleCTG

class GUI:
    def __init__(self):
        self.backend_dict = {}
        self.server_on = False
        self.loading = False
        self.prev_architecture = 0
        self.qasm_file = ''
        self.projection_map = {}

gui = GUI()

def print_me(sender, data):
    """
    Callback for menu items.
    """
    core.log_debug("Menu Item: {}".format(sender))

def createTokenFile(sender, data):
    """
    Creates a new token.txt files and writes token to it.
    """
    token = core.get_value("##token")
    with open('token.txt', 'w') as token_f:
        token_f.write(token)
    core.delete_item('Enter you personal token from IBM website')
    test()

def progress_async(sender, data):
    """
    Fills progress bar.
    """
    counter = 0.0
    while (not gui.server_on):
        core.set_value('progress', value=counter)
        counter += 0.001
        time.sleep(0.001)


def activate_IBM_account(token=""):
    """
    Activates IBM account so the backends list can be fetched.
    """
    if not token:
        raise ValueError('No personal token for authentication')
    # TOKEN = 'd3ea16a94139c07aac8b34dc0a5d4d999354b232118788f43abe6c1414ce9b92a89194d5e7488a0fc8bce644b08927e85c4f127cd973cb32e76fc0d1a766758b'
    IBMQ.enable_account(token)


def get_backends_async(sender, data):
    """
    Fills the backend_dict.
    """
    activate_IBM_account(token=data)
    backends = IBMQ.get_provider().backends()
    # add backend names with indexes, so it will be easier to retrieve them in radio button
    for i in range(len(backends)):
        gui.backend_dict[i] = backends[i].name()
    gui.server_on = True
    gui.loading = True


def show_button(sender, data):
    """
    Displays all the elements after connecting to IBM.
    """
    if (gui.server_on):
        if (gui.loading):
            core.delete_item('Please wait')
            gui.loading = False
        core.configure_item('File Selector', show=True)
        core.configure_item('File location:', show=True)
        core.configure_item('##filedir', show=True)
        core.configure_item('File name:', show=True)
        core.configure_item('##file', show=True)
        core.configure_item('Architecture type:', show=True)
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


def set_default(sender, data):
    """
    resets all running parameters to default.
    """
    if core.get_value('device_type') == 0:
        core.add_spacing(name='##space9', count=2)
        core.add_text('Architecture name:', before='##space5')
        core.add_radio_button('radio##3', items=list(gui.backend_dict.values())[
                              1:], source='architecture', before='##space5')
    core.set_value('device_type', 1)
    core.set_value('architecture', 1)
    core.set_value('layout_type', 1)
    core.set_value('opt_level', 1)
    core.set_value('num_of_iter', 100)


def process(sender, data):
    """
    Sends the data to SimpleCTG.
    """
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
        architecture = gui.backend_dict[0]
    else:
        architecture = gui.backend_dict[core.get_value('architecture') + 1]

    try:
        infoStr, circuit_features = SimpleCTG.gui_interaction(
            file_directory, directory, layout_type, opt_level, architecture, num_of_iter
        )
        # show program output
        core.configure_item(
            'Program output will be displayed here', color=[255, 255, 255])
        core.draw_image('input_circuit', circuit_features['logical_graph'], [
                        0, 500], pmax=[200, 500])
        core.draw_image('output_circuit', circuit_features['reduced_graph'], [
                        0, 500], pmax=[200, 500])
        gui.qasm_file = circuit_features['qasm_file']
        core.set_value('circuitImage', circuit_features['ibm_circuit'])
        gui.projection_map = circuit_features['mapping']
        core.set_value('Program output will be displayed here',
                       "Processed file: " + core.get_value('file_directory') + "\n" + infoStr)
        core.configure_item('Open qasm file', show=True)
        core.configure_item('Mapping', show=True)
        core.configure_item('Path to IBM circuit representation', show=True)
        core.configure_item(
            'circuitImage', value=core.get_value('circuitImage'))
    except Exception as ex:
        # if error, then makes text red and removes features
        core.configure_item(
            'Program output will be displayed here', color=[255, 0, 0])
        core.set_value('Program output will be displayed here', "Processed file: " +
                       core.get_value('file_directory') + "\n" + traceback.format_exc())
        core.clear_drawing('input_circuit')
        core.clear_drawing('output_circuit')
        core.configure_item('Open qasm file', show=False)
        core.configure_item('Mapping', show=False)
        core.configure_item('circuitImage', show=False)
        core.configure_item('Path to IBM circuit representation', show=False)

def use_arbitrary_coupling(sender, data):
    # TODO:
    print('-')


def add_IBM_computers_view():
    core.add_spacing(name='##space9', count=2)
    core.add_text('Architecture name:', before='##space5')
    core.add_radio_button('radio##3', items=list(gui.backend_dict.values())[
                            1:], source='architecture', before='##space5')
    gui.prev_architecture = 1


def add_arbitrary_coupling_view():
    core.add_input_text('##architectureWindow', multiline=True, show=False)
    core.add_button('Use', callback=use_arbitrary_coupling)
    gui.prev_architecture = 2


def delete_IBM_computers_view():
    core.delete_item('##space9')
    core.delete_item('Architecture name:')
    core.delete_item('radio##3')
    gui.prev_architecture = 0


def delete_arbitrary_coupling_view():
    core.delete_item('##architectureWindow')
    core.delete_item('Use')
    gui.prev_architecture = 0


def show_architecture_list(sender, data):
    """
    Makes architecture list dynamic.
    """
    my_var = core.get_value('device_type')
    core.log_debug(my_var)
    if (my_var == 0):
        if (gui.prev_architecture == 1):
            delete_IBM_computers_view()
        if (gui.prev_architecture == 2):
            delete_arbitrary_coupling_view()

    elif (my_var == 1 and gui.prev_architecture != 1):
        add_IBM_computers_view()
        if (gui.prev_architecture == 2):
            delete_arbitrary_coupling_view()

    elif (my_var == 2 and gui.prev_architecture != 2):
        add_arbitrary_coupling_view()
        if (gui.prev_architecture == 1):
            delete_IBM_computers_view()


def file_picker(sender, data):
    """
    Opens file dialog window to choose .pla file
    """
    core.open_file_dialog(callback=apply_selected_directory, extensions='.real')


def apply_selected_directory(sender, data):
    """
    Sets the file name
    """
    directory = data[0]
    file_directory = data[1]
    core.set_value('directory', directory)
    core.set_value('file_directory', file_directory)


def delete_items(data):
    """
    Removes the window name.

    Parameters:
    data (List[str]): items to be deleted
    """
    for item in data:
        core.delete_item(item)


def open_qasm(sender, data):
    """
    Opens window with qasm code
    """
    with simple.window('Qasm code', width=400, height=600, on_close=delete_items(['Qasm code'])):
        with open(gui.qasm_file, 'r') as f:
            core.add_text(f.read())


def help_show_architectures(sender, data):
    """
    Switch to architecture tab
    """
    core.configure_item('helpArchitectures', show=True)
    core.configure_item('helpShowInstructions', show=False)


def help_show_instructions(sender, data):
    """
    Switch to instructions tab
    """
    core.configure_item('helpShowInstructions', show=True)
    core.configure_item('helpArchitectures', show=False)


def open_help_window(sender, data):
    """
    Opens new window with help annotations
    """
    with simple.window('Help##window', width=1000, height=600, on_close=delete_items(['Help##window'])):
        with simple.menu_bar("Help Menu Bar"):
            core.add_menu_item("Architectures", callback=help_show_architectures)
            core.add_menu_item("Instructions", callback=help_show_instructions)

        with simple.group('helpArchitectures'):
            core.add_drawing('armonk', width=72, height=75)
            core.draw_image('armonk', './backends/armonk.png', [72, 72])
            core.add_text('ibmq_armonk: 1 qubit.')
            core.add_spacing(name='##space10', count=10)

            core.add_drawing('athens', width=518, height=75)
            core.draw_image(
                'athens', './backends/athens-santiago.png', [0, 72])
            core.add_text('ibmq_athens and ibmq_santiago: 5 qubits.')
            core.add_spacing(name='##space10', count=10)

            core.add_drawing('yorktown', width=373, height=400)
            core.draw_image('yorktown', './backends/ibmqx2.png', [0, 400])
            core.add_text('ibmqx2: 5 qubits.')
            core.add_spacing(name='##space10', count=10)

            core.add_drawing('melb', width=1000, height=196)
            core.draw_image('melb', './backends/melbourne.png', [0, 196])
            core.add_text('ibmq_16_melbourne: 15 qubits.')
            core.add_spacing(name='##space10', count=10)

            core.add_drawing('vigo', width=373, height=400)
            core.draw_image(
                'vigo', './backends/vigo-ourence-valencia.png', [0, 400])
            core.add_text(
                'ibmq_vigo, ibmq_valencia, and ibmq_ourence: 5 qubits.')
            core.add_spacing(name='##space10', count=10)

        with simple.group('helpInstructions', show="False"):
            core.add_text(
                'In the Selector block a user can select optimization parameters:')
            core.add_text(
                '* the level of optimization provided by IBM Q (ranging from 0 to 3)')
            core.add_text('* IBM Original layout or advanced SWAP placement')
            core.add_text('* location of placement')
            core.add_text('* number of iterations.')

            instruction_text = """In the Hardware & Circuit block the user can choose between testing the circuit on a quantum computer (IBM Q) and simulator (Qasm). The user also can choose quantum coupling (quantum computer architecture) - from IBM Q or Qasm. Finally, there is a button to upload an input file.  After selection, the file name will be displayed in the Hardware & Circuit block and the circuit representation will be displayed in the Circuit before the reduction block. When pressing on the Process button the tool will find the optimal mapping of the circuit onto the quantum computer architecture. The resulting mapping will appear in the Circuit after the reduction block."""
            count = 0
            step = 120
            while (count + step) < len(instruction_text):
                core.add_text(instruction_text[count: count + step])
                if instruction_text[count + step] != ' ' and instruction_text[count + step] != '-':
                    core.add_same_line()
                    core.add_text('-')
                count += step


def open_about_window(sender, data):
    """
    Opens new window with credentials
    """
    with simple.window('About##window', width=600, height=240, on_close=delete_items(['About##window'])):
        core.add_text('Developers:')
        core.add_text(
            '* Valeriy Novossyolov [Computer Science senior student, Nazarbayev University]')
        core.add_text(
            '* Saadat Nursultan [Computer Science senior student, Nazarbayev University]')
        core.add_spacing(name='##space10', count=5)
        core.add_text('Adviser:')
        core.add_text(
            '* Martin Lukac [Associate Professor, Dep. of Computer Science, Nazarbayev University]')
        core.add_spacing(name='##space10', count=5)
        core.add_text('Developed to support the scientific paper')
        core.add_text(
            "'Geometric Refactoring of Quantum and Reversible Circuits: Quantum Layout'")
        core.add_text(
            'by Martin Lukac, Saadat Nursultan, Georgiy Krylov and Oliver Keszocze')


def show_mapping(sender, data):
    """
    Opens new window with a mapping.
    """
    if core.get_value('device_type') == 0:
        architecture = gui.backend_dict[0]
    else:
        architecture = gui.backend_dict[core.get_value('architecture') + 1]

    old_dict = gui.projection_map
    new_dict = dict([(value, key) for key, value in old_dict.items()])     
    draw_graph(architecture, new_dict)
    

def draw_graph(architecture, mapping, diameter=20):
    """
    Draws a physical architecture and labels mapped nodes.

    Parameters: 
    architecture (str): Architecture type.
    mapping (dict): Mapping from circuit graph to pysical architecture.
    diameter (float): Diameter of the graph nodes. Also determines the size of resulting graph.

    Returns: 
    None 
    """
    with simple.window('Graph', width=800, height=800, on_close=delete_items(['Graph', 'drawing1'])):
        core.add_drawing('drawing1', width=int(
            diameter*diameter*2), height=int((diameter/2)**2))

    start_x = diameter
    start_y = diameter * 4
    color_white = [255, 255, 255, 255]
    color_black = [0, 0, 0, 255]
    color_orange = [255, 170, 23, 255]
    color_blue = [15, 27, 115, 255]
    line_width = 5

    num_of_nodes = {
        architecture == 'ibmq_armonk': 1,
        architecture == 'ibmq_athens' or
        architecture == 'ibmq_santiago' or
        architecture == 'ibmqx2' or
        architecture == 'ibmq_vigo' or
        architecture == 'ibmq_valencia' or
        architecture == 'ibmq_ourence': 5,
        architecture == 'ibmq_16_melbourne': 15
    }[True]

    ###
    if architecture == 'ibmq_armonk':
        # draw one node
        core.draw_circle('drawing1', [start_x, start_y],
                         diameter, color_orange, fill=color_orange)
        core.draw_text('drawing1', [start_x - diameter, start_y + (
            diameter / 2)], mapping[0], color=color_black, size=diameter)

    ###
    elif architecture == 'ibmq_athens' or architecture == 'ibmq_santiago':
        for k in range(num_of_nodes):
            if k in mapping.keys():
                core.draw_circle(
                    'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
                core.draw_text('drawing1', [start_x - diameter, start_y + (
                    diameter / 2)], mapping[k], color=color_black, size=diameter)
            else:
                core.draw_circle(
                    'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
                core.draw_text('drawing1', [start_x - diameter, start_y + (
                    diameter / 2)], str(k), color=color_blue, size=diameter)
            # draw an edge only if it is not the last node
            if k < 4:
                core.draw_line("drawing1", [start_x + diameter, start_y], [
                               start_x + (diameter * 2), start_y], color_white, line_width)
                start_x += diameter * 3

    ###
    elif architecture == 'ibmq_vigo' or architecture == 'ibmq_valencia' or architecture == 'ibmq_ourence':
        for k in range(num_of_nodes):
            if k == 2:
                # save previous coordinates
                previous_x, previous_y = start_x, start_y
                # adjust coordinates
                start_x -= (diameter * 3)
                start_y -= (diameter * 3)
                if k in mapping.keys():
                    core.draw_circle(
                        'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
                    core.draw_text('drawing1', [start_x - diameter, start_y + (
                        diameter / 2)], mapping[k], color=color_black, size=diameter)
                else:
                    core.draw_circle(
                        'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
                    core.draw_text('drawing1', [start_x - diameter, start_y + (
                        diameter / 2)], str(k), color=color_blue, size=diameter)
                core.draw_line("drawing1", [start_x, start_y + diameter], [
                               start_x, start_y + (diameter * 2)], color_white, line_width)
                # restore coordinates
                start_x, start_y = previous_x, previous_y
            else:
                if k in mapping.keys():
                    core.draw_circle(
                        'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
                    core.draw_text('drawing1', [start_x - diameter, start_y + (
                        diameter / 2)], mapping[k], color=color_black, size=diameter)
                else:
                    core.draw_circle(
                        'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
                    core.draw_text('drawing1', [start_x - diameter, start_y + (
                        diameter / 2)], str(k), color=color_blue, size=diameter)
                # draw an edge only if it is not the last node
                if k < 4:
                    core.draw_line("drawing1", [start_x + diameter, start_y], [
                                   start_x + (diameter * 2), start_y], color_white, line_width)
                    start_x += diameter * 3

    ###
    elif architecture == 'ibmqx2':
        k = 0
        start_y = diameter
        if k in mapping.keys():
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
            core.draw_text('drawing1', [start_x - diameter, start_y + (
                diameter / 2)], mapping[k], color=color_black, size=diameter)
        else:
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
            core.draw_text('drawing1', [start_x - diameter, start_y + (
                diameter / 2)], str(k), color=color_blue, size=diameter)
        core.draw_line("drawing1", [start_x, start_y + diameter],
                       [start_x, start_y + (diameter * 2)], color_white, line_width)
        k += 1
        start_y += diameter * 3
        if k in mapping.keys():
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
            core.draw_text('drawing1', [start_x - diameter, start_y + (
                diameter / 2)], mapping[k], color=color_black, size=diameter)
        else:
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
            core.draw_text('drawing1', [start_x - diameter, start_y + (
                diameter / 2)], str(k), color=color_blue, size=diameter)
        k += 1
        start_x += diameter * 3
        start_y -= diameter * 1.5
        if k in mapping.keys():
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
            core.draw_text('drawing1', [start_x - diameter, start_y + (
                diameter / 2)], mapping[k], color=color_black, size=diameter)
        else:
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
            core.draw_text('drawing1', [start_x - diameter, start_y + (
                diameter / 2)], str(k), color=color_blue, size=diameter)
        core.draw_line("drawing1", [start_x + (diameter / 2) + 5, start_y - (diameter / 2) - 5], [
                       start_x + (diameter * 2), start_y - (diameter * 1.5)], color_white, line_width)
        core.draw_line("drawing1", [start_x + (diameter / 2) + 5, start_y + (diameter / 2) + 5], [
                       start_x + (diameter * 2), start_y + (diameter * 1.5)], color_white, line_width)
        core.draw_line("drawing1", [start_x - (diameter / 2) - 5, start_y - (diameter / 2) - 5], [
                       start_x - (diameter * 2), start_y - (diameter * 1.5)], color_white, line_width)
        core.draw_line("drawing1", [start_x - (diameter / 2) - 5, start_y + (diameter / 2) + 5], [
                       start_x - (diameter * 2), start_y + (diameter * 1.5)], color_white, line_width)
        k += 1
        start_x += diameter * 3
        start_y += diameter * 1.5
        if k in mapping.keys():
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
            core.draw_text('drawing1', [start_x - diameter, start_y + (
                diameter / 2)], mapping[k], color=color_black, size=diameter)
        else:
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
            core.draw_text('drawing1', [start_x - diameter, start_y + (
                diameter / 2)], str(k), color=color_blue, size=diameter)
        k += 1
        start_y -= diameter * 3
        if k in mapping.keys():
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
            core.draw_text('drawing1', [start_x - diameter, start_y + (
                diameter / 2)], mapping[k], color=color_black, size=diameter)
        else:
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
            core.draw_text('drawing1', [start_x - diameter, start_y + (
                diameter / 2)], str(k), color=color_blue, size=diameter)
        core.draw_line("drawing1", [start_x, start_y + diameter],
                       [start_x, start_y + (diameter * 2)], color_white, line_width)

    ###
    elif architecture == 'ibmq_16_melbourne':
        start_y = diameter
        for k in range(num_of_nodes):
            temp_key = num_of_nodes - (k + 1)

            if temp_key in mapping.keys():
                core.draw_circle(
                    'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
                temp_key = num_of_nodes - (k + 1)
                core.draw_text('drawing1', [start_x - diameter, start_y + (
                    diameter / 2)], mapping[temp_key], color=color_black, size=diameter)
            else:
                core.draw_circle(
                    'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
                core.draw_text('drawing1', [start_x - diameter, start_y + (
                    diameter / 2)], str(temp_key), color=color_blue, size=diameter)

            if k != 7 and k != 8:
                core.draw_line("drawing1", [start_x + diameter, start_y], [
                               start_x + (diameter * 2), start_y], color_white, line_width)

            if (k < 7):
                core.draw_line("drawing1", [start_x, start_y + diameter], [
                               start_x, start_y + (diameter * 2)], color_white, line_width)
                start_x += diameter * 3
            else:
                start_x -= diameter * 3

            if (k == 7):
                start_y += diameter * 3


def test():

    with open('token.txt', 'r') as token_file:
        token = token_file.readline()
        try:
            # Connect to IBM
            core.run_async_function(get_backends_async, data=token)
            core.set_render_callback(show_button)

            # Progress bar
            with simple.window('Please wait', no_scrollbar=True, height=70, width=400, x_pos=500, y_pos=200):
                core.add_progress_bar('progress', value=0.0,
                                    overlay='Connecting to IBM...', width=400)
                core.run_async_function(progress_async, 0)

            # Title
            core.add_text('Quantum visualization machine ver 1.0.0',
                        color=[52, 73, 235])
            core.add_spacing(name='##space1', count=5)

            # Menu bar
            with simple.menu_bar("Main Menu Bar"):

                with simple.menu("File"):

                    core.add_menu_item("Save", callback=print_me)
                    core.add_menu_item("Save As", callback=print_me)

                core.add_menu_item("Help", callback=open_help_window)
                core.add_menu_item("About", callback=open_about_window)

            # Parameters group
            with simple.group('left group', width=300):
                # Select file button
                core.add_button('File Selector', callback=file_picker, show=False)
                core.add_spacing(name='##space2', count=3)
                core.add_text('File location:', show=False)
                core.add_label_text('##filedir', value='None Selected',
                                    source='directory', show=False)
                core.add_spacing(name='##space3', count=3)
                core.add_text('File name:', show=False)
                core.add_label_text('##file', value='None Selected',
                                    source='file_directory', show=False)
                core.add_spacing(name='##space4', count=3)
                # Architecture type radio button
                core.add_text('Architecture type:', show=False)
                core.add_radio_button('radio##1', items=[
                                    'IBM simulator', 'IBM quantum computer', 'Arbitrary computer coupling'], callback=show_architecture_list, source='device_type', show=False)
                core.add_spacing(name='##space5', count=3)
                # Layout radio button
                core.add_text('Quantum circuit layout method:', show=False)
                core.add_radio_button('radio##2', items=[
                                    'Original IBM layout', 'Advanced SWAP placement'], source='layout_type', show=False)
                core.add_spacing(name='##space6', count=3)
                # Optimization level slider
                core.add_text('Optimization level:', show=False)
                core.add_slider_int('##optimization_lvl', default_value=1, min_value=0, max_value=3,
                                    tip='drag the slider to select an optimization level', width=300, source='opt_level', show=False)
                core.add_spacing(name='##space7', count=3)
                # Number of iterations slider
                core.add_text('Number of iterations:', show=False)
                core.add_slider_int('##num_of_iter', default_value=100, min_value=1, max_value=100,
                                    tip='drag the slider to number of iterations', width=300, source='num_of_iter', show=False)
                core.add_spacing(name='##space8', count=3)
                # Default settings button
                core.add_button('Set Default', callback=set_default, show=False)
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
                core.add_button('Open qasm file', callback=open_qasm, show=False)
                core.add_text('Path to IBM circuit representation', show=False)
                core.add_label_text('circuitImage')
                core.add_button('Mapping', callback=show_mapping, show=False)
                core.add_text('Program output:', show=False)
                core.add_text('Program output will be displayed here',
                            show=False, wrap=440)
            
        except Exception as exc:
            print("[ERROR]: {}".format(exc))


if __name__ == '__main__':
    core.add_additional_font('Karla-Regular.ttf', 20)
    core.set_main_window_size(1500, 900)

    # check if there is a file
    if not os.path.isfile('token.txt'):
        with simple.window('Enter you personal token from IBM website', no_scrollbar=True, height=70, width=400, x_pos=500, y_pos=200):
                    core.add_input_text("##token", width=380)
                    core.add_button("Enter", callback=createTokenFile)    
    else:
        test()
           
    core.start_dearpygui()           

