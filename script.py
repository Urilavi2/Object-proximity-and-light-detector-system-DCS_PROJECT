import PySimpleGUI as sg
import serial as ser
import time

Commands = {"inc_lcd": "0x01", "dec_lcd": "0x02", "rra_lcd": "0x03", "set_delay": "0x04", "clear_lcd": "0x05",
            "servo_deg": "0x06", "servo_scan": "0x07", "sleep": "0x07"}
Converted_file = []
# s = ser.Serial('COM3', baudrate=9600, bytesize=ser.EIGHTBITS,
    #                parity=ser.PARITY_NONE, stopbits=ser.STOPBITS_ONE,
    #                timeout=1)   # timeout of 1 sec so that the read and write operations are blocking,
    #                             # when the timeout expires the program will continue

    # CHANGE THE COM!!

EnableTX = True


def checkfile(path):
    file = open(path, 'r')
    file_content = file.read()  # str of the whole file
    temp = file_content.split("\n")
    i = 0
    while temp[i]:
        try:
            command = temp[i].split(" ")
            if command[0] not in Commands:
                return False  # not a valid command!!
            elif command[0] == "sleep" or command[0] == "clear_lcd":
                try:
                    command[1] = 0  # checking that there is no number next to these Commands
                    return False
                except Exception:  # all good!
                    Converted_file[i] = Commands.get(command[0]) + "\n"
                    i = i + 1
                    continue
            elif command[0] == "servo_deg":
                if int(command[1]) < 0 or int(command[1]) > 180:
                    return False
                else:  # all good!
                    Converted_file[i] = Commands.get(command[0]) + hex(int(command[1])) + "\n"
                    i = i+1
                    continue
            elif command[0] == "servo_scan":
                command[1] = command[1].split(",")  # if there is no argument in command[1] then the file is not good
                                                    # and will go to the except block
                if type(command[1] is list):
                    if int(command[1][0]) < 0 or int(command[1][0]) > 180:
                        return False
                    else:  # all good!
                        Converted_file[i] = Commands.get(command[0]) + hex(int(command[1][0])) + hex(int(command[1][1])) + "\n"
                        i = i + 1
                        continue
                else:
                    return False
            else:
                int(command[1])   # making sure that the operand is a number!
                Converted_file[i] = Commands.get(command[0]) + hex(int(command[1])) + "\n"
                i = i + 1
        except Exception:
            return False
    return True


def sendfile(script_num):
    s.reset_output_buffer()
    s.reset_input_buffer()
    EnableTX = True
    while (s.out_waiting > 0 or EnableTX):
        bytetxscript = bytes(script_num + '\n', 'ascii')
        s.write(bytetxscript)
        time.sleep(0.25)  # delay for accurate read/write operations on both ends
        if s.out_waiting == 0:
            EnableTX = False
    s.reset_output_buffer()
    EnableTX = True
    commands_count = len(Converted_file)
    i=0
    while (s.out_waiting > 0 or EnableTX):
        bytetxcommand = bytes(Converted_file[i], 'ascii')
        s.write(bytetxcommand)
        time.sleep(0.25)  # delay for accurate read/write operations on both ends
        i = i+1
        if i == commands_count:
            EnableTX = False


def activescript(script_num):
    s.reset_output_buffer()
    s.reset_input_buffer()
    while (s.out_waiting > 0 or EnableTX):
        bytetxscript = bytes(script_num + '\n', 'ascii')
        s.write(bytetxscript)
        time.sleep(0.25)  # delay for accurate read/write operations on both ends
        if s.out_waiting == 0:
            EnableTX = False


def ScriptMenu():
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

        # if event == "_S1_":
        #     activescript('1')
        #
        #     # NEED TO ADDRESS AN ERROR GOT FROM MCU VIA WHILE LOOP OF READING --> meaning there is no script saved
        #
        #     # ASSUMING NO ERROR OCCURRED  --> SCRIPT IS RUNNING OK  -->  need to read from MCU acknowledge
                # and read requests from MCU when commands servo_scan and servo_deg are coming and act as well
        #
        # if event == "_S2_":
        #     activescript('2')

        #     # NEED TO ADDRESS AN ERROR GOT FROM MCU VIA WHILE LOOP OF READING
        #
        #     # ASSUMING NO ERROR OCCURRED  --> SCRIPT IS RUNNING OK
        #
        # if event == "_S3_":
        #     activescript('3')

        #     # NEED TO ADDRESS AN ERROR GOT FROM MCU VIA WHILE LOOP OF READING
        #
        #     # ASSUMING NO ERROR OCCURRED  --> SCRIPT IS RUNNING OK

    window.close()
