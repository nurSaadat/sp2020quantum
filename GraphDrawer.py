import dearpygui.core as core
import dearpygui.simple as simple


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
    with simple.window('Graph', width=800, height=800):
        core.add_drawing('drawing1', width=int(diameter*diameter*2), height=int((diameter/2)**2))

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
        core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
            diameter / 2)], mapping[0], color=color_black, size=diameter)

    ###
    elif architecture == 'ibmq_athens' or architecture == 'ibmq_santiago':
        for k in range(num_of_nodes):
            if k in mapping.keys():
                core.draw_circle(
                    'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
                core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                    diameter / 2)], mapping[k], color=color_black, size=diameter)
            else:
                core.draw_circle(
                    'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
                core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
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
                    core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                        diameter / 2)], mapping[k], color=color_black, size=diameter)
                else:
                    core.draw_circle(
                        'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
                    core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                        diameter / 2)], str(k), color=color_blue, size=diameter)
                core.draw_line("drawing1", [start_x, start_y + diameter], [
                               start_x, start_y + (diameter * 2)], color_white, line_width)
                # restore coordinates
                start_x, start_y = previous_x, previous_y
            else:
                if k in mapping.keys():
                    core.draw_circle(
                        'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
                    core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                        diameter / 2)], mapping[k], color=color_black, size=diameter)
                else:
                    core.draw_circle(
                        'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
                    core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
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
            core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                diameter / 2)], mapping[k], color=color_black, size=diameter)
        else:
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
            core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                diameter / 2)], str(k), color=color_blue, size=diameter)
        core.draw_line("drawing1", [start_x, start_y + diameter],
                       [start_x, start_y + (diameter * 2)], color_white, line_width)
        k += 1
        start_y += diameter * 3
        if k in mapping.keys():
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
            core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                diameter / 2)], mapping[k], color=color_black, size=diameter)
        else:
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
            core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                diameter / 2)], str(k), color=color_blue, size=diameter)
        k += 1
        start_x += diameter * 3
        start_y -= diameter * 1.5
        if k in mapping.keys():
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
            core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                diameter / 2)], mapping[k], color=color_black, size=diameter)
        else:
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
            core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
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
            core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                diameter / 2)], mapping[k], color=color_black, size=diameter)
        else:
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
            core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                diameter / 2)], str(k), color=color_blue, size=diameter)
        k += 1
        start_y -= diameter * 3
        if k in mapping.keys():
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_orange, fill=color_orange)
            core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                diameter / 2)], mapping[k], color=color_black, size=diameter)
        else:
            core.draw_circle(
                'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
            core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
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
                core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
                    diameter / 2)], mapping[temp_key], color=color_black, size=diameter)
            else:
                core.draw_circle(
                    'drawing1', [start_x, start_y], diameter, color_white, fill=color_white)
                core.draw_text('drawing1', [start_x - (diameter / 2), start_y + (
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


if __name__ == '__main__':
    diameter = 30
    architecture = 'ibmq_16_melbourne'
    mapping = {
        1: 'a',
        2: 'b',
        3: 'd'
    }
    draw_graph(architecture, mapping, diameter=diameter)
    core.start_dearpygui()
