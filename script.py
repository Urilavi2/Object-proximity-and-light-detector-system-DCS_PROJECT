import PySimpleGUI as sg
import serial as ser
import time
import math

Commands = {"inc_lcd": "01", "dec_lcd": "02", "rra_lcd": "03", "set_delay": "04", "clear_lcd": "05",
            "servo_deg": "06", "servo_scan": "07", "sleep": "08"}
Converted_file = []
s = ser.Serial('COM3', baudrate=9600, bytesize=ser.EIGHTBITS,
               parity=ser.PARITY_NONE, stopbits=ser.STOPBITS_ONE,
               timeout=1)   # timeout of 1 sec so that the read and write operations are blocking,
                            # when the timeout expires the program will continue

# CHANGE THE COM!!

enableTX = True
GRAPH_SIZE = (450, 450)

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
    file = open(path, 'r')
    file_content = file.read()  # str of the whole file
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
                    Converted_file.append(Commands.get(command[0]) + "\n")
                    i = i + 1
                    continue
            elif command[0] == "servo_deg":
                if int(command[1]) < 0 or int(command[1]) > 180:
                    return False
                else:  # all good!
                    op1 = hex(int(command[1]))[2:]
                    if len(op1) < 2:
                        op1 = '0' + op1
                    Converted_file.append(Commands.get(command[0]) + op1 + "\n")
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
                        Converted_file.append(Commands.get(command[0]) + op1 + op2 + "\n")
                        i = i + 1
                        continue
                else:
                    return False
            else:
                int(command[1])  # making sure that the operand is a number!
                op1 = hex(int(command[1]))[2:]
                if len(op1) < 2:
                    op1 = '0' + op1
                Converted_file.append(Commands.get(command[0]) + op1 + "\n")
                i = i + 1
        except Exception:
            return False
    return True


def sendfile(script_num):
    global s, enableTX, Converted_file
    s.reset_output_buffer()
    s.reset_input_buffer()
    enableTX = True
    # sending a bit to MCU to tell him that file is about to be sent
    s.write(bytes('s\n', 'ascii'))
    while s.out_waiting > 0 or enableTX:
        bytetxscript = bytes(script_num + '\n', 'ascii')
        s.write(bytetxscript)
        time.sleep(0.25)  # delay for accurate read/write operations on both ends
        if s.out_waiting == 0:
            enableTX = False
    s.reset_output_buffer()
    enableTX = True
    commands_count = len(Converted_file)
    i = 0
    while s.out_waiting > 0 or enableTX:
        bytetxcommand = bytes(Converted_file[i], 'ascii')
        s.write(bytetxcommand)
        time.sleep(0.25)  # delay for accurate read/write operations on both ends
        i = i + 1
        if i == commands_count:
            enableTX = False
    while s.in_waiting > 0:
        byteack = s.readline()
        if byteack.decode("ascii") == '1':
            print('received script No. ' + script_num)
    #  ADD ACKNOWLEDGE RECEIVE!!!!!!


def activescript(script_num):
    global s, enableTX
    s.reset_output_buffer()
    s.reset_input_buffer()
    while (s.out_waiting > 0 or enableTX):
        bytetxscript = bytes(script_num + '\n', 'ascii')
        s.write(bytetxscript)
        time.sleep(0.25)  # delay for accurate read/write operations on both ends
        if s.out_waiting == 0:
            enableTX = False
    while True:
        while s.in_waiting > 0:
            readerbyte = s.read(size=1)
            reader = readerbyte.decode("ascii")
            if reader == '1':
                return True
            if reader == '0':
                sg.popup("No file in memory!")
                return False


def readcommands():
    active = True
    obj_window = 0
    tele_window = 0
    while active:
        while s.in_waiting > 0:
            bytesomething = s.readline()
            something = bytesomething.decode("ascii")
            if something == 's':  # AKA scan
                if tele_window != 0:
                    tele_window.close()
                    tele_window = 0
                obj_window = object_window()
            elif something == 'd':  # AKA degree
                if obj_window != 0:
                    obj_window.close()
                    obj_window = 0
                angle_read = False
                while not angle_read:
                    while s.in_waiting > 0:
                        anglebyte = s.readline()
                        angle = anglebyte.decode("ascii")
                        angle_read = True
                tele_window = telem_window(angle)
                angle_read = False
            elif something == 'f':  # AKA finish
                if obj_window != 0:
                    obj_window.close()
                if tele_window != 0:
                    tele_window.close()
                active = False


def telem_window(str_angle):
    global s, enableTX
    layout = [[sg.T('    ', font="any 34 bold "),
               sg.T('Telemeter', font="any 34 bold underline", text_color='red', pad=(120, 10))],
              [sg.T('', key='_ANGLE_', pad=(100, 10), font='any 14'),],
              [sg.T('', key='_DISTANCE_', pad=(100, 10), font='any 14')],
              [sg.B("Main Menu", pad=(250, 20))]
              ]
    str_distance = '0'
    window = sg.Window('Telemeter', layout, size=(600, 250))
    window.finalize()
    window['_ANGLE_'].update('Known angle: ' + str_angle + '°')
    window['_DISTANCE_'].update('Distance: ' + str_distance + ' cm')
    while True:
        event, values = window.read()
        while s.in_waiting > 0:
            charByte = s.readline()  # expect to find '\n' in the end of the distance!
            str_distance = str(charByte.decode("ascii"))
            if s.in_waiting == 0:
                enableTX = True
            window['_DISTANCE_'].update('Distance: ' + str_distance + ' cm')
            return window

def object_window():
    global s, enableTX, objects
    layout = [
        [sg.T("        Object Detector", font="any 30 bold", text_color='red', size=(0, 1))],
        [sg.T("              System", font="any 30 bold", text_color='red')],
        [sg.T(" ", size=(1, 2))],
        [sg.T("", font="any 14", key="_DISTANCE_")],
        [sg.T(" ", size=(1, 2))],
        [sg.Graph(canvas_size=GRAPH_SIZE, graph_top_right=GRAPH_SIZE, graph_bottom_left=(0, 0),
                  background_color='black', key="_GRAPH_")],
        [sg.B("Main Menu", pad=(130, 20))]
    ]
    window = sg.Window('Object Proximity Detector', layout)
    window.finalize()
    window['_DISTANCE_'].update('                      Max Distance: 450 cm')
    graph = window["_GRAPH_"]

    graph.draw_arc((10, -160), (440, 360), 180, 0, style='arc', arc_color='green')
    graph.draw_arc((60, -110), (390, 310), 180, 0, style='arc', arc_color='green')
    graph.draw_arc((110, -60), (340, 260), 180, 0, style='arc', arc_color='green')
    graph.DrawLine((10, 100), (440, 100), width=2, color="white")
    x_offset = 225
    y_offset = 100  # graph
    scan = True
    printscan = False
    # tx to mcu to start sweep
    startSweep()
    #  end of sending start sweep bit
    while True:
        event, values = window.read(timeout=300, timeout_key="_TIMEOUT_")
        #  0.3 second timeout for now, need to calculate the time to first send

        if event == '_TIMEOUT_' and scan:
            while scan:
                i = 0
                info = [0, 0]
                # RX
                while s.in_waiting > 0:  # while the input buffer isn't empty
                    enableTX = False
                    temp = s.readline()
                    # receive until '\n' -> first receive the distance (time differences) and then the angle
                    info[i] = int(temp.decode("ascii"))
                    i = i + 1
                if i == 3:
                    i = 0
                    real_info = (int(info[0] / 58), int(info[1]))
                    objects.append(real_info)
                    # print(char.decode("ascii"))  # just for debugging
                    if s.in_waiting == 0:
                        enableTX = True
                        scan = False  # need to make sure that s.in_waiting is not empty between sending distance and angle
                        printscan = True
            #  END OF RX
            if printscan:
                for i in range(0, len(objects)):
                    distance = objects[i][0]
                    angle = math.radians(objects[i][1])
                    print(distance * math.cos(angle) * 0.47 + x_offset,
                          distance * math.sin(angle) * 0.58 + y_offset)
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
                objects.clear()
                return window


def ScriptMenu():
    global Converted_file
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
    window = sg.Window('Script Mode', layout)

    while True:
        Converted_file.clear()  # cleaning the variable for the next load
        event, values = window.read()
        if event in (None, "Main Menu"):
            break
        if event == "_F1SUB_":
            if not checkfile(values["_F1_"]):
                sg.popup("File is not valid!")
                continue
            else:
                sendfile('1')

        if event == "_F2SUB_":
            if not checkfile(values["_F2_"]):
                sg.popup("File is not valid!")
                continue
            else:
                sendfile('2')

        if event == "_F3SUB_":
            if not checkfile(values["_F3_"]):
                sg.popup("File is not valid!")
                continue
            else:
                sendfile('3')

        if event == "_S1_":
            ack = activescript('1')
            if ack:
                readcommands()
                ack = False
                # read requests from MCU when commands servo_scan and servo_deg are coming and act as well
        # ASSUMING NO ERROR OCCURRED  --> SCRIPT IS RUNNING OK  -->  need to read from MCU acknowledge  -- recieved in activescript
        if event == "_S2_":
            ack = activescript('2')
            if ack:
                readcommands()
                ack = False
                # read requests from MCU when commands servo_scan and servo_deg are coming and act as well
            # ASSUMING NO ERROR OCCURRED  --> SCRIPT IS RUNNING OK
        if event == "_S3_":
            ack = activescript('3')
            if ack:
                readcommands()
                ack = False
                # read requests from MCU when commands servo_scan and servo_deg are coming and act as well
            # ASSUMING NO ERROR OCCURRED  --> SCRIPT IS RUNNING OK

    window.close()
