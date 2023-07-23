import PySimpleGUI as sg
import serial as ser
import math
import Object
import light

number_of_scan = 21
Str_distance = '450'
angle_calc = lambda angle: int((angle - 350) / 10)  # 1800 = 2150 -350
sound_speed = (331.3 + 0.606 * 35) * 100
range_cm = lambda cycles: (sound_speed / 2) * cycles * (1 / (2 ** 20))
margin = 1800

global s
enableTX = True

scaleX = 2
scaleY = 1.4
GRAPH_SIZE = (450*scaleX, int(450*scaleY)-100)

objects = []


def popup(message):
    layout = [[sg.Text(message, font="any 16", text_color="red")]]
    window = sg.Window('Message', layout, no_titlebar=True, keep_on_top=True, finalize=True)
    return window


def popup_new_dis(message):
    layout = [[sg.Text(message)], [sg.T("                    "), sg.B('Ok', size=(6,2))]]
    window = sg.Window('Message', layout, no_titlebar=True, keep_on_top=True, finalize=True)
    return window


# def calibration(scan,s):      NOT IN USE!!!

#     # calibration of both LDR1 and LDR2, computing average of every point in space on MCU and send result
#     light.ldr_calibrated.clear()
#     light.ldr_measurement.clear()
#     global enableTX, calibrated
#     start_scan = popup_new_dis("                     SET DISTANCE!\n\nmeasurement will not continue until 'Ok' pressed")
#     eventD, valD = start_scan.read()
#     while eventD != 'Ok':
#         continue
#     start_scan.close()
#     enableTX = True
#     while s.out_waiting > 0 or enableTX:
#         bytetxMsg = bytes('r' + '\n', 'ascii')  # 'r' for MCU is to continue
#         s.write(bytetxMsg)
#         if s.out_waiting == 0:
#             enableTX = False
#     calibrate = popup("Calibrating...")
#     calibrate.refresh()
#     while(1):
#         while s.in_waiting > 0 and scan:  # while the input buffer isn't empty
#             enableTX = False
#             temp = s.readline()
#             char = temp.decode("utf-8")
#             print(char)
#             if char == 'E':
#                 error_scan = popup_new_dis(
#                     "        ERROR IN SCAN!        TRY AGAIN!\n\nmeasurement will not continue until 'Ok' pressed")
#                 eventD, valD = error_scan.read()
#                 while eventD != 'Ok':
#                     continue
#                 error_scan.close()
#                 enableTX = True
#                 while s.out_waiting > 0 or enableTX:
#                     bytetxMsg = bytes('r' + '\n', 'ascii')  # 'r' for MCU is to continue
#                     s.write(bytetxMsg)
#                     if s.out_waiting == 0:
#                         enableTX = False
#             elif char == 'n':
#                 change_dis = popup_new_dis("                  CHANGE DISTANCE!\n\nmeasurement will not continue until 'Ok' pressed")
#                 eventD, valD = change_dis.read()
#                 while eventD != 'Ok':
#                     continue
#                 change_dis.close()
#                 enableTX = True
#                 while s.out_waiting > 0 or enableTX:
#                     bytetxMsg = bytes('r' + '\n', 'ascii')  # 'r' for MCU is to continue
#                     s.write(bytetxMsg)
#                     if s.out_waiting == 0:
#                         enableTX = False
#             elif char == 'd':  # calibration done
#                 calibrate.close()
#                 print("ldr_measurement:\n", light.ldr_measurement)
#                 sg.popup("Calibration finished!", auto_close=True, auto_close_duration=1, any_key_closes=True)
#                 for j in range(0, 10):
#
#                     for i in range(0, 5):
#                         if j != 0:
#                             m = int(light.ldr_measurement[j]) - int(light.ldr_measurement[j - 1]) / 5
#                         else:
#                             m = int(light.ldr_measurement[j+1]) - int(light.ldr_measurement[j]) / 5
#                         light.ldr_calibrated.append((i * m) + light.ldr_measurement[j])
#                 enableTX = True
#                 calibrated = True
#                 print("ldr_calibrated:\n", light.ldr_calibrated)
#                 return True
#             else:
#                 print("this is distance: ", len(light.ldr_measurement))
#                 light.ldr_measurement.append((int(char) / light.N_ADC))  # reading from MCU LDR average results

def lights_objects(com):
    ldr_scan = []
    object_array = []
    global Str_distance, objects, enableTX, s
    s = com
    list_window = False
    scan_objects = False
    scan = True
    scan_objects = False
    printscan = False
    x_offset = 225 * scaleX
    y_offset = int(100 * scaleY) - 100
    while not light.calibrated:
        light.calibrated = light.calibration(scan, s)
        if light.break_calibration:
            return
    if light.calibrated:
        light.objects.clear()  # in case there was a light scan before...

        light.startSweep('r', s)  # sending 'r' to start scan sweep!
        # ----------------------> in this scan, MCU saves both LDR average results and objects proximity in 2 arrays

        light.scanning(scan, ldr_scan,s)  # MCU sends ldr scan results
        scan_objects = True
        light.startSweep('r',s)  # wake up MCU after sending all of ldr scans

        Object.scanning(scan, objects,s)  # MCU sends objects scan results
        scan = False
        printscan = True

        #  end of receiving all objects and light in space

    # Define the layout
    layout = [
        [sg.T("Light Sources And Object", font="any 30 bold", text_color='red', size=(0, 1))],
        [sg.T("        Detector System", font="any 30 bold", text_color='red')],
        # [sg.T(" ", size=(1, 0))],
        [sg.T("", font="any 14", key="_DISTANCE_"), sg.B('change', button_color=('dark blue', 'white'))],
        [sg.T("                     "), sg.T("legend:", font="any 10 underline"),
         sg.T("O", text_color="light blue", font="any 11 bold"),
         sg.T("- light source  ,"), sg.T("X", text_color="purple", font="any 11 bold"), sg.T("- object")],
        # [sg.T(" ", size=(1, 0))],
        [sg.Graph(canvas_size=GRAPH_SIZE, graph_top_right=GRAPH_SIZE, graph_bottom_left=(0, 0),
                  background_color='black', key="_GRAPH_", pad=(25, 0))],
        [sg.B("Rescan!", pad=(25, 0)), sg.T('                    '),
         sg.B("List of Objects", key="_OBJECTS_"), sg.T('                    '), sg.B('calibration')],
        [sg.B("Main Menu", pad=(210, 0), size=(10, 2))]
    ]
    window = sg.Window('Objects and Lights Detector', layout, location=(300, 0))
    window.finalize()
    window['_DISTANCE_'].update(
        '                                                              Limit Distance: ' + Str_distance + ' cm')
    graph = window["_GRAPH_"]

    graph.draw_arc((10 * scaleX, int(-160 * scaleY) - 100), (440 * scaleX, int(360 * scaleY) - 100), 180, 0,
                   style='arc', arc_color='green')
    graph.draw_arc((60 * scaleX, int(-110 * scaleY) - 100), (390 * scaleX, int(310 * scaleY) - 100), 180, 0,
                   style='arc', arc_color='green')
    graph.draw_arc((110 * scaleX, int(-60 * scaleY) - 100), (340 * scaleX, int(260 * scaleY) - 100), 180, 0,
                   style='arc', arc_color='green')
    graph.DrawLine((10 * scaleX, int(100 * scaleY) - 100), (440 * scaleX, int(100 * scaleY) - 100), width=2,
                   color="white")


    while True:
        event, values = window.read(timeout=50, timeout_key="_TIMEOUT_")
        #  worked with timeout=200 (with no push button read!), change timeout to 50 cause of calibration button

        if event == '_TIMEOUT_' and not light.calibrated:
            sg.popup("need to calibrate LDRs first!!", font="any 20 bold", auto_close=True, auto_close_duration=1.5,
                     text_color="dark red", button_type=5, no_titlebar=True)

        if event == '_TIMEOUT_':
            while s.in_waiting > 0:
                enableTX = False
                temp = s.read()
                char = temp.decode("utf-8")
                print("char: ", char, "char[0]: ", char[0])
                if char[0] == 'c':
                    s.reset_input_buffer()
                    light.calibrated = light.calibration(True, s)
                    if light.break_calibration:
                        light.break_calibration = False
                        break
                    else:
                        printscan = True

            if light.calibrated:
                if printscan:
                    # establish objects list
                    print('printing on screen!')
                    print("objects list:\n", objects)
                    objects.append('Q')
                    # the letter Q is to differ between objects and lights in the completed objects list
                    for i in range(0, len(ldr_scan)):
                        voltage = ldr_scan[i][0]
                        if voltage > 5:
                            continue
                        for j in range(0, len(light.ldr_calibrated)):
                            if abs(light.ldr_calibrated[j] - voltage) < 0.017:  # PLAY WITH MARGIN!
                                #  add a differ between light and object in the same palce feature
                                objects.append((j, ldr_scan[i][1]))

                    # objects list is ready with lights objects
                    print("lights and objects list ready:\n", objects)

                    for i in range(0, len(objects)):
                        try:
                            # if objects[i] is 'Q' there is no objects[i][1]. we will get an Exception (objects[i][0] = 'Q')
                            distance = objects[i][0]
                            angle = math.radians(objects[i][1])
                        except Exception:
                            print("end of objects....\nstarting to add lights to graph")
                            scan_objects = False
                            continue
                        if scan_objects:
                            if distance <= int(Str_distance) and distance > 1:
                                # print("OBJECT:")                                                            ---> DEBUGGING
                                # print("x: ", distance * math.cos(angle) * 0.47 + x_offset, "y: ",           ---> DEBUGGING
                                #       distance * math.sin(angle) * 0.58 + y_offset)                         ---> DEBUGGING
                                # print("distance: ", distance, "angle: ", math.ceil(math.degrees(angle)))    ---> DEBUGGING
                                graph.draw_text("X", location=(
                                    distance * math.cos(angle) * (43/90) * scaleX + x_offset,
                                    distance * math.sin(angle) * (26/45) * scaleY + y_offset),
                                    # 225 is offset of x-axis and 43/90 = 430/900,  430 from 900/2-20
                                    # +100 is the height of the base line and 26/45 = 260/450 where 260 is the max of the arc
                                                font="any 14", color="purple")
                                if (math.ceil(math.degrees(angle))) > 160:
                                    text_offset = 15
                                elif (math.ceil(math.degrees(angle))) < 20:
                                    text_offset = -15
                                else:
                                    text_offset = 0
                                graph.draw_text(f'({int(distance)}, {math.ceil(math.degrees(angle))}°)', location=(
                                    distance * math.cos(angle) * (43/90) * scaleX + x_offset + text_offset,
                                    distance * math.sin(angle) * (26/45) * scaleY + y_offset - 15),
                                                font="any 9", color="white")

                            else:    # ADDING LIGHTS TO GRAPH
                                if distance <= int(Str_distance):
                                    graph.draw_text("O", location=(
                                        distance * math.cos(angle) * (43/90) * scaleX + x_offset,
                                        distance * math.sin(angle) * (26/45) * scaleY + y_offset),
                                                    # NO 'TIMES 9' FOR SCALING like in light file
                                    # 225 is offset of x-axis and 43/90 = 430/900,  430 from 900/2-20
                                    # +100 is the height of the base line and 26/45 = 260/450 where 260 is the max of the arc
                                                    font="any 14", color="light blue")
                                    if (math.ceil(math.degrees(angle))) > 160:
                                        text_offset = 8
                                    elif (math.ceil(math.degrees(angle))) < 20:
                                        text_offset = -8
                                    else:
                                        text_offset = 0
                                    graph.draw_text(f'({int(distance)}, {math.ceil(math.degrees(angle))}°)', location=(
                                        distance * math.cos(angle) * 0.47 * scaleX + x_offset + text_offset,
                                        distance * math.sin(angle) * 0.61 * scaleY + y_offset - 15),
                                                    font="any 9", color="white")
                            window["_GRAPH_"].update()
                            printscan = False

        if event in (None, "Main Menu"):
            objects.clear()
            light.objects.clear()
            break

        if event == "change":
            str_distance_temp = Object.LimitChange()
            if str_distance_temp is None:
                continue

            if light.calibrated:
                Str_distance = str_distance_temp
                window['_DISTANCE_'].update('                    Limit Distance: ' + Str_distance + ' cm')
                scan = True
                printscan = False
                objects.clear()
                light.objects.clear()
                ldr_scan.clear()
                graph.erase()
                graph.draw_arc((10 * scaleX, int(-160 * scaleY) - 100), (440 * scaleX, int(360 * scaleY) - 100), 180, 0,
                               style='arc', arc_color='green')
                graph.draw_arc((60 * scaleX, int(-110 * scaleY) - 100), (390 * scaleX, int(310 * scaleY) - 100), 180, 0,
                               style='arc', arc_color='green')
                graph.draw_arc((110 * scaleX, int(-60 * scaleY) - 100), (340 * scaleX, int(260 * scaleY) - 100), 180, 0,
                               style='arc', arc_color='green')
                graph.DrawLine((10 * scaleX, int(100 * scaleY) - 100), (440 * scaleX, int(100 * scaleY) - 100), width=2,
                               color="white")

                light.startSweep('r', s)  # sending 'r' to start scan sweep!
                # ------------------> in this scan, MCU saves both LDR average results and objects proximity in 2 arrays

                window.hide()
                light.scanning(scan, ldr_scan, s)  # MCU sends ldr scan results
                while not light.calibrated:  # if received 'c' from push button during the scan
                    light.calibrated = light.calibration(scan, s)
                    if light.break_calibration:  # if hit Cancel in the calibration mode stay with the last calibration
                        light.calibrated = True
                        enableTX = True
                        while s.out_waiting > 0 or enableTX:
                            bytetxMsg = bytes('d' + '\n', 'ascii')
                            # 'd' for MCU is to tell that ldr are calibrated and calibration function is canceled
                            s.write(bytetxMsg)
                            if s.out_waiting == 0:
                                enableTX = False
                        break
                    objects.clear()
                    ldr_scan.clear()
                    light.scanning(scan, ldr_scan, s)
                if light.break_calibration:  # if hit Cancel in the calibration mode stay with the last calibration
                    light.break_calibration = False
                    continue
                scan_objects = True
                light.startSweep('r', s)  # wake up MCU after sending all of ldr scans
                Object.scanning(scan, objects, s)  # MCU sends objects scan results
                window.un_hide()
                scan = False
                printscan = True
            else:
                sg.popup("need to calibrate LDRs first!!", font="any 20 bold", auto_close=True, auto_close_duration=1.5,
                         text_color="dark red", button_type=5, no_titlebar=True)

        if event == 'calibration':
            light.calibrated = light.calibration(scan, s)
            if light.break_calibration:
                light.break_calibration = False
                continue
            objects.clear()
            light.objects.clear()
            ldr_scan.clear()
            scan = True
            printscan = False
            graph.erase()
            graph.draw_arc((10 * scaleX, int(-160 * scaleY) - 100), (440 * scaleX, int(360 * scaleY) - 100), 180, 0,
                           style='arc', arc_color='green')
            graph.draw_arc((60 * scaleX, int(-110 * scaleY) - 100), (390 * scaleX, int(310 * scaleY) - 100), 180, 0,
                           style='arc', arc_color='green')
            graph.draw_arc((110 * scaleX, int(-60 * scaleY) - 100), (340 * scaleX, int(260 * scaleY) - 100), 180, 0,
                           style='arc', arc_color='green')
            graph.DrawLine((10 * scaleX, int(100 * scaleY) - 100), (440 * scaleX, int(100 * scaleY) - 100), width=2,
                           color="white")

            light.startSweep('r', s)  # sending 'r' to start scan sweep!
            # ------------------> in this scan, MCU saves both LDR average results and objects proximity in 2 arrays
            window.hide()
            light.scanning(scan, ldr_scan,s)  # MCU sends ldr scan results

            while not light.calibrated:  # if received 'c' from push button during the scan
                light.calibrated = light.calibration(scan, s)
                if light.break_calibration:  # if hit Cancel in the calibration mode stay with the last calibration
                    light.calibrated = True
                    enableTX = True
                    while s.out_waiting > 0 or enableTX:
                        bytetxMsg = bytes('d' + '\n', 'ascii')
                        # 'd' for MCU is to tell that ldr are calibrated and calibration function is canceled
                        s.write(bytetxMsg)
                        if s.out_waiting == 0:
                            enableTX = False
                    break
                objects.clear()
                ldr_scan.clear()
                light.scanning(scan, ldr_scan, s)
            if light.break_calibration:  # if hit Cancel in the calibration mode stay with the last calibration
                light.break_calibration = False
                continue
            scan_objects = True
            light.startSweep('r', s)  # wake up MCU after sending all of ldr scans

            Object.scanning(scan, objects, s)  # MCU sends objects scan results
            window.un_hide()
            scan = False
            printscan = True

        if event == "Rescan!":
            if light.calibrated:
                scan = True
                printscan = False
                objects.clear()
                light.objects.clear()
                ldr_scan.clear()
                graph.erase()
                graph.draw_arc((10 * scaleX, int(-160 * scaleY) - 100), (440 * scaleX, int(360 * scaleY) - 100), 180, 0,
                               style='arc', arc_color='green')
                graph.draw_arc((60 * scaleX, int(-110 * scaleY) - 100), (390 * scaleX, int(310 * scaleY) - 100), 180, 0,
                               style='arc', arc_color='green')
                graph.draw_arc((110 * scaleX, int(-60 * scaleY) - 100), (340 * scaleX, int(260 * scaleY) - 100), 180, 0,
                               style='arc', arc_color='green')
                graph.DrawLine((10 * scaleX, int(100 * scaleY) - 100), (440 * scaleX, int(100 * scaleY) - 100), width=2,
                               color="white")

                light.startSweep('r',s)  # sending 'r' to start scan sweep!
                # ------------------> in this scan, MCU saves both LDR average results and objects proximity in 2 arrays
                window.hide()
                light.scanning(scan, ldr_scan,s)  # MCU sends ldr scan results

                while not light.calibrated:  # if received 'c' from push button during the scan
                    light.calibrated = light.calibration(scan, s)
                    if light.break_calibration:  # if hit Cancel in the calibration mode stay with the last calibration
                        light.calibrated = True
                        enableTX = True
                        while s.out_waiting > 0 or enableTX:
                            bytetxMsg = bytes('d' + '\n', 'ascii')
                            # 'd' for MCU is to tell that ldr are calibrated and calibration function is canceled
                            s.write(bytetxMsg)
                            if s.out_waiting == 0:
                                enableTX = False
                        break
                    objects.clear()
                    ldr_scan.clear()
                    light.scanning(scan, ldr_scan, s)
                if light.break_calibration:  # if hit Cancel in the calibration mode stay with the last calibration
                    light.break_calibration = False
                    continue
                scan_objects = True
                light.startSweep('r', s)  # wake up MCU after sending all of ldr scans

                Object.scanning(scan, objects, s)  # MCU sends objects scan results
                window.un_hide()
                scan = False
                printscan = True
            else:
                sg.popup("need to calibrate LDRs first!!", font="any 20 bold", auto_close=True, auto_close_duration=1.5,
                         text_color="dark red", button_type=5, no_titlebar=True)

        if event == "_OBJECTS_":
            if not list_window:
                objects_str = ''
                list_of_objects_layout = [[sg.T("List Of Objects", font="any 20 bold underline", text_color="red")],
                                          [sg.T('', key="_SOURCE_")], [sg.B("close")]]
                                            #sg.T("distance: " + str(objects[i][0]) + " cm," "  angle: " + str(objects[i][1]) + "°",
                                                 #text_color="white")] for i in range(0,len(objects)) if
                                           #(1 < objects[i][0] <= int(Str_distance))],
                q_flag = 0
                for i in range(0, len(objects)):
                    if objects[i][0] == 'Q':
                        q_flag = 1
                        continue
                    if q_flag == 0:
                        objects_str = objects_str + "object: " "distance: " + str(objects[i][0]) + " cm," "  angle: " + str(objects[i][1]) + "°\n"
                    else:
                        objects_str = objects_str + "light: " "distance: " + str(
                            objects[i][0]) + " cm," "  angle: " + str(objects[i][1]) + "°\n"

                list_of_objects_window = sg.Window('Objects list', list_of_objects_layout)
                window.hide()
                list_of_objects_window["_SOURCE_"].update(objects_str)
                Oevent, Oval = list_of_objects_window.read()

                list_window = True

        if list_window:
            if Oevent in (None, "close"):
                list_of_objects_window.close()
                list_window = False
                window.un_hide()

    window.close()
