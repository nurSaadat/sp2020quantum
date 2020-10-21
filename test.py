import dearpygui.core as core
import dearpygui.simple as simple

def showArchitectureList(sender, data):
    my_var = core.get_value(sender)
    if (my_var):
        core.add_text("Architecture name:")
        core.add_checkbox("chris", parent="left group")
    else:
        core.delete_item("chris")

def filePicker(sender, data):
    core.open_file_dialog(callback=applySelectedDirectory, extensions=".real")

def applySelectedDirectory(sender, data):
    directory = data[0]
    file_directory = data[1]
    core.add_label_text("##filedir", value="None Selected", source="directory", before="File name:")
    core.add_label_text("##file", value="None Selected", source="file_directory", before="Device type:")
    core.set_value("directory", directory)
    core.set_value("file_directory", file_directory)

    # if file_directory == "test.py":
    #     core.draw_circle("Input circuit", [10, 100], 10, [0, 255, 0, 255])

def transCircuit(sender, data):
    core.clear_drawing("Output circuit")
    core.draw_rectangle("Output circuit", [0, 0], [300, 200], [255, 255, 255, 255], [255, 255, 255, 255], tag="background")
    core.draw_line("Output circuit", [0, 100], [300, 100], [255, 0, 0, 255], 1, tag="circuit line")
    
    offset = 0
    if core.get_value("Rectangle"):
        core.draw_rectangle("Output circuit", [0 + offset, 90], [20 + offset, 110], [0, 255, 0, 255])
        offset += 20
    if core.get_value("Triangle"):
        core.draw_triangle("Output circuit", [0 + offset, 90], [0 + offset, 110], [20 + offset, 100], [0, 255, 0, 255])
        offset += 20
    if core.get_value("Line"):
        core.draw_line("Output circuit", [0 + offset, 90], [20 + offset, 110], [0, 255, 0, 255], 1)
        offset += 20
    if core.get_value("Circle"):
        core.draw_circle("Output circuit", [10 + offset, 100], 10, [0, 255, 0, 255])


if __name__ == "__main__":

    with simple.group("left group", width=400):
        core.add_button("File Selector", callback=filePicker) 
        core.add_text("File location:")
        
        core.add_text("File name:")
        
        core.add_text("Device type:")
        core.add_checkbox("IBM simulator")
        core.add_checkbox("IBM quantum computer", callback=showArchitectureList)
        core.add_text("Quantum circuit layout method:")
        core.add_radio_button("radio##1", items=["Original IBM layout", "Advanced SWAP placement"])
        core.add_text("Optimization level:")
        core.add_slider_int("##optimization_lvl", default_value=1, min_value=0, max_value=3, tip="drag the slider to select an optimization level")
        core.add_text("Number of iterations:")
        core.add_slider_int("##num_of_iter", default_value=100, min_value=1, max_value=100, tip="drag the slider to number of iterations")
        

    # core.add_same_line(spacing=100)

    # with simple.group("right group"):
    #     core.add_text("Input circuit:")
    #     core.add_drawing("Input circuit", width=300, height=200)
    #     core.add_button("Transform", callback=transCircuit)
    #     core.add_text("Output circuit:")
    #     core.add_drawing("Output circuit", width=300, height=200)

    #     core.draw_rectangle("Input circuit", [0, 0], [300, 200], [255, 255, 255, 255], [255, 255, 255, 255], tag="background")
    #     core.draw_line("Input circuit", [0, 100], [300, 100], [255, 0, 0, 255], 1, tag="circuit line")

    #     core.draw_rectangle("Output circuit", [0, 0], [300, 200], [255, 255, 255, 255], [255, 255, 255, 255], tag="background")
    #     core.draw_line("Output circuit", [0, 100], [300, 100], [255, 0, 0, 255], 1, tag="circuit line")
    core.show_logger()
    core.start_dearpygui()