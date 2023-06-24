import PySimpleGUI as sg
import serial as ser
import time
import math

Str_distance = '450'

# s = ser.Serial('COM3', baudrate=9600, bytesize=ser.EIGHTBITS,
#                    parity=ser.PARITY_NONE, stopbits=ser.STOPBITS_ONE,
#                    timeout=1)   # timeout of 1 sec so that the read and write operations are blocking,
#                                 # when the timeout expires the program will continue

#     # CHANGE THE COM!!
#  also change line 95 (explain comment is in line 96) as needed
#  notice line 116

enableTX = True

GRAPH_SIZE = (450, 450)

objects = []


def LimitChange():
    layout = [[sg.T('Wanted Distance: '), sg.I(key='_INPUT_', size=(8, 1))],
              [sg.B('Ok'), sg.B('Cancel')]]
    window = sg.Window('Limit Updater', layout)
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            window.close()
            return None
        if event == 'Ok':
            try:
                new_limit = int(values['_INPUT_'])
                if new_limit < 0 or new_limit > 450:
                    sg.popup("Distance must be: \n\n- bigger then 0\n- smaller then 450\n\n Press any key to close",
                             any_key_closes=True)
                    continue
                window.close()
                return values['_INPUT_']
            except Exception:
                sg.popup(
                    "Distance must be: \n\n- AN INTEGER!\n\n- bigger then 0\n- smaller then 450\n\n Press any key to close",
                    any_key_closes=True)


def startSweep():
    global enableTX
    global s
    # tx to mcu to start sweep
    enableTX = True
    s.reset_output_buffer()
    s.reset_input_buffer()
    while s.out_waiting > 0 or enableTX:  # while the output buffer isn't empty
        bytetxMsg = bytes('1' + '\n', 'ascii')  # '1' for MCU is to start sweep
        s.write(bytetxMsg)
        if s.out_waiting == 0:
            enableTX = False
    #  end of sending start sweep bit

def Object():
    global Str_distance, objects, enableTX, s
    # Define the layout
    layout = [
        [sg.T("        Object Detector", font="any 30 bold", text_color='red', size=(0, 1))],
        [sg.T("              System", font="any 30 bold", text_color='red')],
        [sg.T(" ", size=(1, 2))],
        [sg.T("", font="any 14", key="_DISTANCE_"), sg.B('change', button_color=('dark blue', 'white'))],
        [sg.T(" ", size=(1, 2))],
        [sg.Graph(canvas_size=GRAPH_SIZE, graph_top_right=GRAPH_SIZE, graph_bottom_left=(0, 0),
                  background_color='black', key="_GRAPH_")],
        [sg.B("Rescan!"), sg.B("Main Menu", pad=(130, 20))]
    ]

    window = sg.Window('Object Proximity Detector', layout)
    window.finalize()
    window['_DISTANCE_'].update('                    Limit Distance: ' + Str_distance + ' cm')
    graph = window["_GRAPH_"]

    graph.draw_arc((10, -160), (440, 360), 180, 0, style='arc', arc_color='green')
    graph.draw_arc((60, -110), (390, 310), 180, 0, style='arc', arc_color='green')
    graph.draw_arc((110, -60), (340, 260), 180, 0, style='arc', arc_color='green')
    graph.DrawLine((10, 100), (440, 100), width=2, color="white")
    x_offset = 225
    y_offset = 100
    scan = True
    printscan = False

    # tx to mcu to start sweep
    startSweep()
    #  end of sending start sweep bit
    while True:
        event, values = window.read(timeout=1000, timeout_key="_TIMEOUT_")
                                                #  1 second timeout for now, need to calculate the time to first send

        if event == '_TIMEOUT_' and scan:
            while scan:
                i = 0
                info = [0, 0]
                # RX
                while s.in_waiting > 0:  # while the input buffer isn't empty
                    enableTX = False
                    temp = s.readline()
                    if temp.decode("ascii") == 'd':
                        enableTX = True
                        scan = False  # need to make sure that s.in_waiting is not empty between sending distance and angle
                        printscan = True
                        break
                    # receive until '\n' -> first receive the distance (time differences) and then the angle
                    info[i] = int(temp.decode("ascii"))
                    i = i+1
                if i == 3:
                    i = 0
                    real_info = (int(info[0]/58), int(info[1]))
                    objects.append(real_info)
                    # print(char.decode("ascii"))  # just for debugging

            #  END OF RX
            if printscan:
                for i in range(0, len(objects)):
                    distance = objects[i][0]
                    angle = math.radians(objects[i][1])
                    if distance <= int(Str_distance):
                        print("OBJECT:")
                        print("x: ", distance * math.cos(angle) * 0.47 + x_offset, "y: ",
                              distance * math.sin(angle) * 0.58 + y_offset)
                        print("distance: ", distance, "angle: ", math.ceil(math.degrees(angle)))
                        graph.draw_text("X", location=(
                            distance * math.cos(angle) * 0.47 + x_offset, distance * math.sin(angle) * 0.58 + y_offset),
                                        # 225 is offset of x-axis and 0.47 = 215/450,
                                        # +100 is the height of the base line and 0.58 = 260/450 where 260 is the max of the arc
                                        font="any 14", color="purple")
                        if (math.ceil(math.degrees(angle))) > 160:
                            text_offset = 15
                        elif (math.ceil(math.degrees(angle))) < 20:
                            text_offset = -15
                        else:
                            text_offset = 0
                        graph.draw_text(f'({int(distance)}, {math.ceil(math.degrees(angle))}°)', location=(
                            distance * math.cos(angle) * 0.47 + x_offset + text_offset,
                            distance * math.sin(angle) * 0.58 + y_offset - 15),
                                        font="any 9", color="white")
                        window["_GRAPH_"].update()
                printscan = False

        if event in (None, "Main Menu"):
            break
        if event == "change":
            str_distance_temp = LimitChange()
            if str_distance_temp is None:
                continue
            Str_distance = str_distance_temp
            window['_DISTANCE_'].update('                    Limit Distance: ' + Str_distance + ' cm')
            scan = True
            printscan = False
            graph.erase()
            objects.clear()
            graph.draw_arc((10, -160), (440, 360), 180, 0, style='arc', arc_color='green')
            graph.draw_arc((60, -110), (390, 310), 180, 0, style='arc', arc_color='green')
            graph.draw_arc((110, -60), (340, 260), 180, 0, style='arc', arc_color='green')
            graph.DrawLine((10, 100), (440, 100), width=2, color="white")
            startSweep()

        if event == "rescan!":
            scan = True
            printscan = False
            graph.erase()
            objects.clear()
            graph.draw_arc((10, -160), (440, 360), 180, 0, style='arc', arc_color='green')
            graph.draw_arc((60, -110), (390, 310), 180, 0, style='arc', arc_color='green')
            graph.draw_arc((110, -60), (340, 260), 180, 0, style='arc', arc_color='green')
            graph.DrawLine((10, 100), (440, 100), width=2, color="white")
            startSweep()

    window.close()
