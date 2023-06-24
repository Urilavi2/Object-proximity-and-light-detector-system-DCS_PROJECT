import PySimpleGUI as sg
import serial as ser
import math
import Object
import light

Str_distance = '450'
Str_distance_light = '50'

s = ser.Serial('COM3', baudrate=9600, bytesize=ser.EIGHTBITS,
               parity=ser.PARITY_NONE, stopbits=ser.STOPBITS_ONE,
               timeout=1)  # timeout of 1 sec so that the read and write operations are blocking,
# when the timeout expires the program will continue

# CHANGE THE COM!!

enableTX = True

GRAPH_SIZE = (450, 450)

objects = []


def lights_objects():
    ldr_scan = []
    global Str_distance, objects, enableTX, s
    # Define the layout
    layout = [
        [sg.T("Light Sources And Object", font="any 30 bold", text_color='red', size=(0, 1))],
        [sg.T("        Detector System", font="any 30 bold", text_color='red')],
        [sg.T(" ", size=(1, 0))],
        [sg.T("", font="any 14", key="_DISTANCE_"), sg.B('change', button_color=('dark blue', 'white'))],
        [sg.T("                     "), sg.T("legend:", font="any 10 underline"),
         sg.T("O", text_color="light blue", font="any 11 bold"),
         sg.T("- light source  ,"), sg.T("X", text_color="purple", font="any 11 bold"), sg.T("- object")],
        [sg.T(" ", size=(1, 0))],
        [sg.Graph(canvas_size=GRAPH_SIZE, graph_top_right=GRAPH_SIZE, graph_bottom_left=(0, 0),
                  background_color='black', key="_GRAPH_", pad=(25, 0))],
        [sg.B("Rescan!", pad=(25, 0)), sg.T('                                                                      '),
         sg.B('calibration')],
        [sg.B("Main Menu", pad=(210, 0), size=(10, 2))]
    ]
    window = sg.Window('Objects and Lights Detector', layout, size=(515, 785))
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
    scan_objects = False
    printscan = False
    calibrated = False
    # # tx to mcu to start sweep
    while not calibrated:
        calibrated = light.calibration(scan)
    if calibrated:
        Object.startSweep()
    # #  end of sending start sweep bit
    while True:
        event, values = window.read(timeout=700, timeout_key="_TIMEOUT_")
        #  0.7 second timeout for now, need to calculate the time to first send

        if event == '_TIMEOUT_' and not calibrated:
            sg.popup("need to calibrate LDRs first!!", font="any 20 bold", auto_close=True, auto_close_duration=1.5,
                     text_color="dark red", button_type=5, no_titlebar=True)

        """ THE SCAN: PC receive every LDR scan, in the meanwhile the MCU saves every object scanned in the MCU memory.
                      When finishing sending every LDR scan, objects is being sent"""

        if event == '_TIMEOUT_' and scan and calibrated:
            while scan:
                i = 0
                info = [0, 0]
                # RX of LDRs
                while s.in_waiting > 0:  # while the input buffer isn't empty
                    enableTX = False
                    temp = s.readline()
                    if temp.decode("ascii") == 'o':  # sign for finishing the LDR scan and moving to objects
                        scan = False
                        scan_objects = True
                        break
                    # receive until '\n' -> first receive the LDR average real scan result from MCU
                    # and then the angle of a relevant object
                    info[i] = (int(temp.decode("ascii")))
                    i = i + 1
                if i == 3:
                    i = 0
                    ldr_scan.append((int(info[0]), int(info[1])))
            #  END OF RX of LDRs

            while scan_objects and not scan:
                i = 0
                info = [0, 0]
                # RX of objects
                while s.in_waiting > 0:  # while the input buffer isn't empty
                    enableTX = False
                    temp = s.readline()
                    if temp.decode("ascii") == 'd':
                        enableTX = True
                        scan = False  # need to make sure that s.in_waiting is not empty between sending distance and angle
                        scan_objects = False
                        printscan = True
                        break
                    # receive until '\n' -> first receive the distance (time differences) and then the angle
                    info[i] = int(temp.decode("ascii"))
                    i = i + 1
                if i == 3:
                    i = 0
                    real_info = (int(info[0] / 58), int(info[1]))
                    objects.append(real_info)
            #  END OF RX of objects

            if printscan:  # putting on graph the objects
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

                temp_obj_len = len(objects)
                # appending light sources to objects list
                for i in range(0, len(ldr_scan)):
                    for j in range(0, len(light.ldr_calibrated)):
                        if abs(light.ldr_calibrated[j] - ldr_scan[i][0]) < 10:  # MAYBE LESS THAN 10....
                            objects.append((j, ldr_scan[i][1]))
                # objects list ready

                # putting light sources on graph and printing graph!
                for i in range(temp_obj_len, len(objects)):
                    distance = objects[i][0] + 1
                    angle = math.radians(objects[i][1])
                    if distance <= int(Str_distance):
                        print("LIGHT SOURCE:")
                        print("x: ", distance * math.cos(angle) * 0.47 * 9 + x_offset, "y: ",
                              distance * math.sin(angle) * 0.58 * 9 + y_offset)
                        print("distance: ", distance, "angle: ", math.ceil(math.degrees(angle)))
                        graph.draw_text("O", location=(
                            distance * math.cos(angle) * 0.47 * 9 + x_offset, distance * math.sin(angle) * 0.58 * 9 + y_offset),
                                        # 225 is offset of x-axis and 0.47 = 215/450,
                                        # +100 is the height of the base line and 0.58 = 260/450 where 260 is the max of the arc
                                        font="any 14", color="light blue")
                        if (math.ceil(math.degrees(angle))) > 160:
                            text_offset = 8
                        elif (math.ceil(math.degrees(angle))) < 20:
                            text_offset = -8
                        else:
                            text_offset = 0
                        graph.draw_text(f'({int(distance)}, {math.ceil(math.degrees(angle))}°)', location=(
                            distance * math.cos(angle) * 0.47 * 9 + x_offset + text_offset,
                            distance * math.sin(angle) * 0.58 * 9 + y_offset - 15),
                                        font="any 9", color="white")
                window["_GRAPH_"].update()
                printscan = False

        if event in (None, "Main Menu"):
            break

        if event == "change":
            str_distance_temp = Object.LimitChange()
            if str_distance_temp is None:
                continue
            Str_distance = str_distance_temp
            window['_DISTANCE_'].update('                    Limit Distance: ' + Str_distance + ' cm')
            scan = True
            printscan = False
            objects.clear()
            ldr_scan.clear()
            if calibrated:
                graph.erase()
                graph.draw_arc((10, -160), (440, 360), 180, 0, style='arc', arc_color='green')
                graph.draw_arc((60, -110), (390, 310), 180, 0, style='arc', arc_color='green')
                graph.draw_arc((110, -60), (340, 260), 180, 0, style='arc', arc_color='green')
                graph.DrawLine((10, 100), (440, 100), width=2, color="white")
                Object.startSweep()
            else:
                sg.popup("need to calibrate LDRs first!!", font="any 20 bold", auto_close=True, auto_close_duration=1.5,
                         text_color="dark red", button_type=5, no_titlebar=True)

        if event == 'calibration':
            calibrated = light.calibration(scan)
            objects.clear()
            ldr_scan.clear()
            scan = True
            printscan = False
            Object.startSweep()

        if event == "rescan!":
            scan = True
            printscan = False
            objects.clear()
            ldr_scan.clear()
            if calibrated:
                graph.erase()
                graph.draw_arc((10, -160), (440, 360), 180, 0, style='arc', arc_color='green')
                graph.draw_arc((60, -110), (390, 310), 180, 0, style='arc', arc_color='green')
                graph.draw_arc((110, -60), (340, 260), 180, 0, style='arc', arc_color='green')
                graph.DrawLine((10, 100), (440, 100), width=2, color="white")
                Object.startSweep()
            else:
                sg.popup("need to calibrate LDRs first!!", font="any 20 bold", auto_close=True, auto_close_duration=1.5,
                         text_color="dark red", button_type=5, no_titlebar=True)
    window.close()
