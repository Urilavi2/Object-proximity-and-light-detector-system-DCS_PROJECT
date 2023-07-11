import PySimpleGUI as sg
import serial as ser
import time
import math

Str_distance = '50'

# s = ser.Serial('COM17', baudrate=9600, bytesize=ser.EIGHTBITS,
#                parity=ser.PARITY_NONE, stopbits=ser.STOPBITS_ONE,
#                timeout=1)  # timeout of 1 sec so that the read and write operations are blocking,
# when the timeout expires the program will continue
#
#     # CHANGE THE COM!!
#  also change line 93 (explain line 94), 109 (explain line 110) as needed
#  notice line 115

enableTX = True
calibrated = False
GRAPH_SIZE = (450, 450)

objects = []

ldr_calibrated = []


def calibration(scan):
    # calibration of both LDR1 and LDR2, computing average of every point in space on MCU and send result
    ldr_calibrated.clear()
    global enableTX, s, calibrated
    while s.in_waiting > 0 and not scan:  # while the input buffer isn't empty
        enableTX = False
        temp = s.readline()
        char = temp.decode("ascii")
        if char == 'c':
            calibrate = popup("Calibrating...")
        elif char == 'n':
            change_dis = popup_new_dis("   CHANGE DISTANCE!\n\nmeasurement will not continue until MCU sends data")
            while s.in_waiting == 0:
                continue
            change_dis.close()
        elif char == 'd':  # calibration done
            calibrate.close()
            sg.popup("Calibration finished!", auto_close=True, auto_close_duration=1, any_key_closes=True)
            enableTX = True
            calibrated = True
            return True
        else:
            ldr_calibrated.append(int(char))  # reading from MCU LDR average results


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


def popup(message):
    sg.theme('DarkGrey')
    layout = [[sg.Text(message)]]
    window = sg.Window('Message', layout, no_titlebar=True, finalize=True)
    return window


def popup_new_dis(message):

    layout = [[sg.Text(message)], [sg.B('Ok')]]
    window = sg.Window('Message', layout, no_titlebar=True, keep_on_top=True, finalize=True)
    return window


def light(com):
    global Str_distance, objects, enableTX, s, calibrated
    s = com
    ldr_scan = []
    # Define the layout
    layout = [
        [sg.T("         Light Detector", font="any 30 bold", text_color='red', size=(0, 1))],
        [sg.T("              System", font="any 30 bold", text_color='red')],
        [sg.T(" ", size=(1, 2))],
        [sg.B('calibration', button_color=('dark blue', 'white'), pad=(180, 0), size=(10, 2))],
        [sg.T(" ", size=(1, 2))],
        [sg.Graph(canvas_size=GRAPH_SIZE, graph_top_right=GRAPH_SIZE, graph_bottom_left=(0, 0),
                  background_color='black', key="_GRAPH_")],
        [sg.B("Rescan!"), sg.B("Main Menu", pad=(130, 20))]
    ]

    window = sg.Window('Light Proximity Detector', layout)
    window.finalize()
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
    while not calibrated:
        calibrated = calibration(scan)
    if calibrated:
        startSweep()
    #  end of sending start sweep bit
    while True:
        event, values = window.read(timeout=1000, timeout_key="_TIMEOUT_")
        #  1 second timeout for now, need to calculate the time to first send

        if event == '_TIMEOUT_' and not calibrated:
            sg.popup("need to calibrate LDRs first!!", font="any 20 bold", auto_close=True, auto_close_duration=1.5,
                     text_color="dark red", button_type=5, no_titlebar=True)

        if event == '_TIMEOUT_' and scan and calibrated:
            while scan:
                i = 0
                info = [0, 0]
                # RX
                while s.in_waiting > 0:  # while the input buffer isn't empty
                    enableTX = False
                    temp = s.readline()
                    # receive until '\n' -> first receive the LDR average real scan result from MCU
                    # and then the angle of a relevant object
                    info[i] = (int(temp.decode("ascii")))
                    i = i + 1
                if i == 3:
                    i = 0
                    ldr_scan.append((int(info[0]), int(info[1])))
                    if s.in_waiting == 0:
                        enableTX = True
                        scan = False  # need to make sure that s.in_waiting is not empty between sending distance and angle
                        printscan = True
            #  END OF RX
            if printscan:
                # establish objects list
                for i in range(0, len(ldr_scan)):
                    for j in range(0, len(ldr_calibrated)):
                        if abs(ldr_calibrated[j] - ldr_scan[i][0]) < 10:  # MAYBE LESS THAN 10....
                            objects.append((j, ldr_scan[i][1]))
                # objects list ready
                for i in range(0, len(objects)):
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
            objects.clear()
            break

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
                startSweep()
            else:
                sg.popup("need to calibrate LDRs first!!", font="any 20 bold", auto_close=True, auto_close_duration=1.5,
                         text_color="dark red", button_type=5, no_titlebar=True)

        if event == 'calibration':
            calibrated = calibration(scan)
            objects.clear()
            ldr_scan.clear()
            scan = True
            printscan = False
            startSweep()

    window.close()
    s.close()
