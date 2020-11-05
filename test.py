"""test.py: Implements graphical user interface"""

__author__ = 'Saadat Nursultan'
__email__ = 'saadat.nursultan@nu.edu.kz'

import dearpygui.core as core
import dearpygui.simple as simple
import SimpleCTG 
import time
from qiskit import IBMQ

backend_dict = {}
core.add_value('server_on', False)

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
    core.set_value('server_on', True) 

# fills the backend_dict
def getBackendsAsync(sender, data):
    activateIBMAccount()
    backends = IBMQ.get_provider().backends()
    # add backend names with indexes, so it will be easier to retrieve them in radio button
    for i in range(len(backends)):
        backend_dict[i] = backends[i].name()

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
    core.log_debug("Set to default")

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

    core.log_debug(directory)
    core.log_debug(file_directory)
    core.log_debug(layout_type)
    core.log_debug(opt_level)
    core.log_debug(architecture)
    core.log_debug(num_of_iter)

    infoStr = SimpleCTG.gui_interaction(file_directory, directory, layout_type, opt_level, architecture, num_of_iter)
    # core.add_text(infoStr)
    core.log_debug(infoStr)

# makes architecture list dynamic
def showArchitectureList(sender, data):
    my_var = core.get_value('device_type')
    if (my_var == 1):
        core.add_spacing(name='##space9', count=2)
        core.add_text('Architecture name:', before='##space5')
        core.add_radio_button('radio##3', items=list(backend_dict.values())[1:], source='architecture', before='##space5')
    else:
        core.delete_item('##space9')
        core.delete_item('Architecture name:')
        core.delete_item('radio##3')


def filePicker(sender, data):
    core.open_file_dialog(callback=applySelectedDirectory, extensions='.real')

def applySelectedDirectory(sender, data):
    directory = data[0]
    file_directory = data[1]
    core.set_value('directory', directory)
    core.set_value('file_directory', file_directory)

    ## TODO: showing circuit graph
    ## TODO: showing reduced circuit graph

# def openCircuitGraph():
#     directory = core.get_value('directory')
#     file_directory = core.get_value('file_directory')
    # core.draw_image('Input circuit', './'+file_directory+ )

    

    # if file_directory == 'test.py':
    #     core.draw_circle('Input circuit', [10, 100], 10, [0, 255, 0, 255])

# def transCircuit(sender, data):
#     core.clear_drawing('Output circuit')
#     core.draw_rectangle('Output circuit', [0, 0], [300, 200], [255, 255, 255, 255], [255, 255, 255, 255], tag='background')
#     core.draw_line('Output circuit', [0, 100], [300, 100], [255, 0, 0, 255], 1, tag='circuit line')
    
#     offset = 0
#     if core.get_value('Rectangle'):
#         core.draw_rectangle('Output circuit', [0 + offset, 90], [20 + offset, 110], [0, 255, 0, 255])
#         offset += 20
#     if core.get_value('Triangle'):
#         core.draw_triangle('Output circuit', [0 + offset, 90], [0 + offset, 110], [20 + offset, 100], [0, 255, 0, 255])
#         offset += 20
#     if core.get_value('Line'):
#         core.draw_line('Output circuit', [0 + offset, 90], [20 + offset, 110], [0, 255, 0, 255], 1)
#         offset += 20
#     if core.get_value('Circle'):
#         core.draw_circle('Output circuit', [10 + offset, 100], 10, [0, 255, 0, 255])


if __name__ == '__main__':
    # Connect to IBM
    core.run_async_function(getBackendsAsync, 0)

    # Progress bar
    with simple.window('Please wait', no_scrollbar=True, height=60, width=350, x_pos=500, y_pos=200):
        core.add_text('Close the window when the progressbar stops')
        core.add_progress_bar('progress', value=0.0, overlay='Connecting to IBM...', width=400)
        core.run_async_function(progressAsync, 0)

    # Title
    core.add_text('Quantum visualization machine ver 1.0.0', color=[52, 73, 235])
    core.add_spacing(name='##space1', count=5)

    # Parameters group
    with simple.group('left group'):
        # Select file button
        core.add_button('File Selector', callback=filePicker, width=100) 
        core.add_spacing(name='##space2', count=3)
        core.add_text('File location:')
        core.add_label_text('##filedir', value='None Selected', source='directory')
        core.add_spacing(name='##space3', count=3)
        core.add_text('File name:')
        core.add_label_text('##file', value='None Selected', source='file_directory')
        core.add_spacing(name='##space4', count=3)
        # Device type radio button
        core.add_text('Device type:')
        core.add_radio_button('radio##1', items=['IBM simulator', 'IBM quantum computer'], callback=showArchitectureList, source='device_type')
        core.add_spacing(name='##space5', count=3)
        # Layout radio button
        core.add_text('Quantum circuit layout method:')
        core.add_radio_button('radio##2', items=['Original IBM layout', 'Advanced SWAP placement'], source='layout_type')
        core.add_spacing(name='##space6', count=3)
        # Optimization level slider
        core.add_text('Optimization level:')
        core.add_slider_int('##optimization_lvl', default_value=1, min_value=0, max_value=3, tip='drag the slider to select an optimization level', width=300, source='opt_level')
        core.add_spacing(name='##space7', count=3)
        # Number of iterations slider
        core.add_text('Number of iterations:')
        core.add_slider_int('##num_of_iter', default_value=100, min_value=1, max_value=100, tip='drag the slider to number of iterations', width=300, source='num_of_iter')
        core.add_spacing(name='##space8', count=3)
        # Default settings button
        core.add_button('Set Default', callback=setDefault, width= 100) 
        

    core.add_same_line(name='line##3', spacing=100)

    with simple.group('right group'):
         # Process button
        core.add_button('Process', callback=process)
        

    # core.add_same_line(name='line##2', spacing=100)

    # with simple.group('right group'):
    #     # Input circuit preview
    #     core.add_text('Input circuit:')
    #     core.add_drawing('Input circuit', width=600, height=400)
    #     # Output circuit view
    #     core.add_text('Output circuit:')
    #     core.add_drawing('Output circuit', width=600, height=400)

        # core.draw_rectangle('Input circuit', [0, 0], [300, 200], [255, 255, 255, 255], [255, 255, 255, 255], tag='background')
        # core.draw_line('Input circuit', [0, 100], [300, 100], [255, 0, 0, 255], 1, tag='circuit line')

        # core.draw_rectangle('Output circuit', [0, 0], [300, 200], [255, 255, 255, 255], [255, 255, 255, 255], tag='background')
        # core.draw_line('Output circuit', [0, 100], [300, 100], [255, 0, 0, 255], 1, tag='circuit line')
    core.show_logger()
    core.start_dearpygui()
    