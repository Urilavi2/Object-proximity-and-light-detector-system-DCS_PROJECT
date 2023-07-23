import PySimpleGUI as sg
import serial as ser
import time
import math

import Object

Commands = {"inc_lcd": "01", "dec_lcd": "02", "rra_lcd": "03", "set_delay": "04", "clear_lcd": "05",
            "servo_deg": "06", "servo_scan": "07", "sleep": "08"}
Converted_file = []
angle_calc = lambda angle: int((int(angle) - 350)/10)  #  1800 = 2150-350
sound_speed = (331.3 + 0.606 * 35) * 100
range_cm = lambda cycles: (sound_speed / 2) * cycles * (1/(2**20))
# CHANGE THE COM!!
global s
enableTX = True
GRAPH_SIZE = (450, 450)
MCU_have_script = [0, 0, 0]
objects = []


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


def checkfile(path):
    global Converted_file
    try:
        file = open(path, 'r')
        file_content = file.read()  # str of the whole file
    except Exception:
        print("No file path")
        return False
    temp = file_content.split("\n")
    i = 0
    while i < len(temp):
        try:
            command = temp[i].split(" ")
            if command[0] not in Commands:
                return False  # not a valid command!!
            elif command[0] == "sleep" or command[0] == "clear_lcd":
                try:
                    command[1] = 0  # checking that there is no number next to these Commands
                    return False
                except Exception:  # all good!
                    Converted_file.append(Commands.get(command[0]))
                    i = i + 1
                    continue
            elif command[0] == "servo_deg":
                if int(command[1]) < 0 or int(command[1]) > 180:
                    return False
                else:  # all good!
                    op1 = hex(int(command[1]))[2:]  # [2:] because of the '0x' we get from hex()
                    if len(op1) < 2:
                        op1 = '0' + op1
                    Converted_file.append(Commands.get(command[0]) + op1.upper())
                    i = i + 1
                    continue
            elif command[0] == "servo_scan":
                command[1] = command[1].split(",")  # if there is no argument in command[1] then the file is not good
                # and will go to the except block
                if type(command[1] is list):
                    if int(command[1][0]) < 0 or int(command[1][0]) > 180:
                        return False
                    else:  # all good!
                        op1 = hex(int(command[1][0]))[2:]
                        op2 = hex(int(command[1][1]))[2:]
                        if len(op1) < 2:
                            op1 = '0' + op1
                        if len(op2) < 2:
                            op2 = '0' + op2
                        Converted_file.append(Commands.get(command[0]) + op1.upper() + op2.upper())
                        i = i + 1
                        continue
                else:
                    return False
            else:
                int(command[1])  # making sure that the operand is a number!
                op1 = hex(int(command[1]))[2:]
                if len(op1) < 2:
                    op1 = '0' + op1
                Converted_file.append(Commands.get(command[0]) + op1.upper())
                i = i + 1
        except Exception:
            return False
    print(Converted_file)
    return True


def sendfile(script_num):
    global s, enableTX, Converted_file
    s.reset_output_buffer()
    s.reset_input_buffer()
    enableTX = True
    ack = False

    while s.out_waiting > 0 or enableTX:
        bytetxscript = bytes(script_num, 'ascii')
        s.write(bytetxscript)
        if s.out_waiting == 0:
            enableTX = False
    s.reset_output_buffer()
    enableTX = True
    # time.sleep(0.25)  # delay for accurate write operations on both ends
    # sending a bit to MCU to tell him that file is about to be sent!
    while s.out_waiting > 0 or enableTX:
        s.write(bytes('r', 'ascii'))
        if s.out_waiting == 0:
            enableTX = False
    enableTX = True
    commands_count = len(Converted_file)
    time.sleep(0.25)  # delay for accurate read/write operations on both ends
    i = 0
    while s.out_waiting > 0 or enableTX:
        bytetxcommand = bytes(Converted_file[i], 'utf-8')  # maybe need to be utf-8 cause it is longer than a character
        s.write(bytetxcommand)
        time.sleep(0.25)  # delay for accurate read/write operations on both ends
        i = i + 1
        if i == commands_count:
            while s.out_waiting or enableTX:
                end_of_script = bytes('!', 'ascii')
                s.write(end_of_script)
                if s.out_waiting == 0:
                    enableTX = False
    while s.in_waiting > 0 or not ack:
        byteack = s.readline()
        if byteack.decode("ascii") == 'd':
            print('received script No. ' + script_num)
            if s.in_waiting == 0:
                ack = True
                enableTX = True
                MCU_have_script[int(script_num)-1] = 1
                sg.popup("MCU got the script file!", no_titlebar=True, auto_close=True,
                         auto_close_duration=1, font="any 20", button_type=5)
                return
    #  ADD ACKNOWLEDGE RECEIVE!!!!!!


def activescript(script_num):  # make the check here, no need for communication
    global s, enableTX
    s.reset_output_buffer()
    s.reset_input_buffer()
    enableTX = True
    while s.out_waiting > 0 or enableTX:
        bytetxscript = bytes(script_num, 'ascii')
        s.write(bytetxscript)
        time.sleep(0.25)  # delay for accurate read/write operations on both ends
        if s.out_waiting == 0:
            enableTX = False
    time.sleep(0.25)  # delay for accurate read/write operations on both ends
    enableTX = True
    while s.out_waiting > 0 or enableTX:
        bytetxscript = bytes('p', 'ascii')
        s.write(bytetxscript)
        time.sleep(0.25)  # delay for accurate read/write operations on both ends
        if s.out_waiting == 0:
            enableTX = False
    if MCU_have_script[int(script_num)-1] == 1:
        return True
    else:
        sg.popup("No file in memory!", no_titlebar=True, auto_close=True, auto_close_duration=1, button_type=5,
                 text_color="red", font="any 16 bold")
        return False


def popup(message):
    """ returns a window template with nothing but text and no titlebar """
    # sg.theme('DarkGrey')
    layout = [[sg.Text(message, font="any 14", text_color="red")]]
    window = sg.Window('Message', layout, no_titlebar=True, finalize=True)
    return window


def readcommands(running_window):
    active = True
    obj_window = 0
    tele_window = 0
    tele_event = 0
    tele_val = 0
    while active:
        event_nothing, val_nothing = running_window.read()
        if obj_window != 0:
            obj_event, obj_val = obj_window.read()
            if obj_event in (None, "Exit"):
                obj_window.close()
                obj_window = 0

        if tele_window != 0:
            tele_event, tele_val = tele_window.read()
            if tele_event in (None, "Exit"):
                tele_window.close()
                tele_window = 0

        while s.in_waiting > 0:
            bytesomething = s.read()
            something = bytesomething.decode("utf-8")
            if something == 's':  # AKA scan
                if obj_window != 0:
                    obj_window.close()
                obj_window = (object_window())
                obj_event, obj_val = obj_window.read()
            elif something == 'd':  # AKA degree
                angle_read = False
                while not angle_read:
                    while s.in_waiting > 0:
                        anglebyte = s.readline()
                        angle = anglebyte.decode("utf-8")  # reading angle from script
                        angle_read = True
                        print("angle received: ", str(angle))
                if telem_window != 0:
                    tele_window.close()
                tele_window = (telem_window(str(angle_calc(angle))))
                tele_event, tele_val = tele_window.read()
            elif something == 'f':  # AKA finish
                return obj_window, tele_window


def telem_window(str_angle):
    global s, enableTX
    layout = [[sg.T('    ', font="any 34 bold "),
               sg.T('Telemeter', font="any 34 bold underline", text_color='red', pad=(120, 10))],
              [sg.T('', key='_ANGLE_', pad=(100, 10), font='any 14'),],
              [sg.T('', key='_DISTANCE_', pad=(100, 10), font='any 14')],
              [sg.B("Exit", pad=(250, 20))]
              ]
    str_distance = '0'
    window = sg.Window('Telemeter', layout, size=(600, 250))
    window.finalize()
    window['_ANGLE_'].update('Known angle: ' + str_angle + '°')
    # window['_DISTANCE_'].update('Distance: ' + str_distance + ' cm')
    scan = True
    while scan:
        while s.in_waiting > 0:
            charByte = s.readline()  # expect to find '\n' in the end of the distance!
            str_distance = str(charByte.decode("utf-8"))
            if s.in_waiting == 0:
                scan = False
                enableTX = True
                window['_DISTANCE_'].update('Distance: ' + str(int(range_cm(str_distance) )) + ' cm')
    return window

def object_window():
    global s, enableTX, objects
    Str_distance = "450"
    layout = [
        [sg.T("        Object Detector", font="any 30 bold", text_color='red', size=(0, 1))],
        [sg.T("              System", font="any 30 bold", text_color='red')],
        [sg.T(" ", size=(1, 2))],
        [sg.T("", font="any 14", key="_ANGLES_")],
        [sg.T(" ", size=(1, 2))],
        [sg.Graph(canvas_size=GRAPH_SIZE, graph_top_right=GRAPH_SIZE, graph_bottom_left=(0, 0),
                  background_color='black', key="_GRAPH_")],
        [sg.B("Exit", pad=(130, 20))]
    ]
    window = sg.Window('Object Proximity Detector', layout)
    window.finalize()
    graph = window["_GRAPH_"]
    got_angles = False
    angles = [0, 0]
    idx = 0
    while not got_angles:
        while s.in_waiting > 0:
            angle = s.readline()
            angle[idx] = int(angle.decode(angle, 'utf-8'))
            if s.in_waiting == 0:
                idx += 1
                got_angles = True
                window['_ANGLES_'].update('        left angle: ', angles[0], "              right angle: ", angles[1])
    scan = True
    # tx to mcu to start sweep
    startSweep()
    Object.scanning(scan, objects, s, angles[0], angles[1])
    #  end
    graph.draw_arc((10, -160), (440, 360), 180, 0, style='arc', arc_color='green')
    graph.draw_arc((60, -110), (390, 310), 180, 0, style='arc', arc_color='green')
    graph.draw_arc((110, -60), (340, 260), 180, 0, style='arc', arc_color='green')
    graph.DrawLine((10, 100), (440, 100), width=2, color="white")
    x_offset = 225
    y_offset = 100  # graph

    for i in range(0, len(objects)):
        distance = objects[i][0]
        angle = math.radians(objects[i][1])
        # if distance > objects[i-1][0] + 6 or distance + 6 < objects[i-1][0] and i != 0:
        #     angle_distinguish += 1
        #     if angle_distinguish > 3:
        #         angle_distinguish = 1
        # else:
        #     angle_distinguish = 1
        if distance <= int(Str_distance) and distance > 1:
            # print("OBJECT:")
            # print("x: ", distance * math.cos(angle) * 0.47 + x_offset, "y: ",
            #       distance * math.sin(angle) * 0.58 + y_offset)
            # print("distance: ", distance, "angle: ", math.ceil(math.degrees(angle)))
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
    return window


def ScriptMenu(com):
    global Converted_file, s
    s = com
    layout = [[sg.T("   Script Mode", font="any 30 bold", text_color='red')],
              [sg.B("Script 1", size=(10, 5), key="_S1_"), sg.B("Script 2", size=(10, 5), key="_S2_"),
               sg.B("Script 3", size=(10, 5), key="_S3_")],
              [sg.Input(key="_F1_", size=(12, 5)), sg.Input(key="_F2_", size=(12, 5)),
               sg.Input(key="_F3_", size=(12, 5))],
              # all the next buttons are the same, just different address
              [sg.FileBrowse(target="_F1_", file_types=(('Text', '*.txt'),), key="_F1BROWSE_", size=(10, 1)),
               sg.FileBrowse(target="_F2_", file_types=(('Text', '*.txt'),), key="_F2BROWSE_", size=(10, 1)),
               sg.FileBrowse(target="_F3_", file_types=(('Text', '*.txt'),), key="_F3BROWSE_", size=(10, 1))],
              [sg.Submit(size=(10, 1), key="_F1SUB_", button_color=("white", "black")),
               sg.Submit(size=(10, 1), key="_F2SUB_", button_color=("white", "black")),
               sg.Submit(size=(10, 1), key="_F3SUB_", button_color=("white", "black"))],
              [sg.B("Main Menu", pad=(110, 20))]
              ]
    obj = 0
    tele = 0
    window = sg.Window('Script Mode', layout)

    while True:
        Converted_file.clear()  # cleaning the variable for the next load
        event, values = window.read(timeout=50, timeout_key="_TIMEOUT_")

        if event == "_TIMEOUT_":
            if obj != 0:
                obj_event, obj_val = obj.read()
                if obj_event in (None, "Exit"):
                    obj.close()
                    obj = 0
            if tele != 0:
                tele_event, tele_val = tele.read()
                if tele_event in (None, "Exit"):
                    tele.close()
                    tele = 0

        if event in (None, "Main Menu"):
            break

        if event == "_F1SUB_":
            if not checkfile(values["_F1_"]):
                sg.popup("File is not valid!", no_titlebar=True, auto_close=True, auto_close_duration=1, button_type=5,
                 text_color="red", font="any 16 bold")
                continue
            else:
                window.refresh()
                sg.popup("sending script file...", auto_close=True, auto_close_duration=3,
                         non_blocking=True, button_type=5, no_titlebar=True)
                sendfile('1')

        if event == "_F2SUB_":
            if not checkfile(values["_F2_"]):
                sg.popup("File is not valid!", no_titlebar=True, auto_close=True, auto_close_duration=1, button_type=5,
                 text_color="red", font="any 16 bold")
                continue
            else:
                window.refresh()
                sg.popup("sending script file...", auto_close=True, auto_close_duration=3,
                         non_blocking=True, button_type=5, no_titlebar=True)
                sendfile('2')

        if event == "_F3SUB_":
            if not checkfile(values["_F3_"]):
                sg.popup("File is not valid!", no_titlebar=True, auto_close=True, auto_close_duration=1, button_type=5,
                 text_color="red", font="any 16 bold")
                continue
            else:
                window.refresh()
                sg.popup("sending script file...", auto_close=True, auto_close_duration=3,
                         non_blocking=True, button_type=5, no_titlebar=True)
                sendfile('3')

        if event == "_S1_":
            ack = activescript('1')
            if ack:
                if obj != 0:
                    obj.close()
                    obj = 0
                if tele != 0:
                    tele.close()
                    tele = 0
                window.hide()
                running_script_window = popup("running script No. 1...")
                obj, tele = readcommands(running_script_window)
                running_script_window.close()
                window.un_hide()
                ack = False
        # ASSUMING NO ERROR OCCURRED  --> SCRIPT IS RUNNING OK  -->  need to read from MCU acknowledge  -- recieved in activescript
        if event == "_S2_":
            ack = activescript('2')
            if ack:
                if obj != 0:
                    obj.close()
                    obj = 0
                if tele != 0:
                    tele.close()
                    tele = 0
                window.hide()
                running_script_window = popup("running script No. 2...")
                obj, tele = readcommands(running_script_window)
                running_script_window.close()
                window.un_hide()
                ack = False
                # read requests from MCU when commands servo_scan and servo_deg are coming and act as well
            # ASSUMING NO ERROR OCCURRED  --> SCRIPT IS RUNNING OK
        if event == "_S3_":
            ack = activescript('3')
            if ack:
                if obj != 0:
                    obj.close()
                    obj = 0
                if tele != 0:
                    tele.close()
                    tele = 0
                window.hide()
                running_script_window = popup("running script No. 3...")
                obj, tele = readcommands(running_script_window)
                running_script_window.close()
                window.un_hide()
                ack = False
                # read requests from MCU when commands servo_scan and servo_deg are coming and act as well
            # ASSUMING NO ERROR OCCURRED  --> SCRIPT IS RUNNING OK

    window.close()
