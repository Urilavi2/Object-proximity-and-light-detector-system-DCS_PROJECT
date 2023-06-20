import PySimpleGUI as sg
import serial as ser
import time
import math

Str_distance = '450'

# s = ser.Serial('COM3', baudrate=9600, bytesize=ser.EIGHTBITS,
#                    parity=ser.PARITY_NONE, stopbits=ser.STOPBITS_ONE,
#                    timeout=1)   # timeout of 1 sec so that the read and write operations are blocking,
#                                 # when the timeout expires the program will continue
#
#     # CHANGE THE COM!!


enableTX = True

GRAPH_SIZE = (450, 450)

objects = [(70, 10), (200,90)]

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
                sg.popup("Distance must be: \n\n- AN INTEGER!\n\n- bigger then 0\n- smaller then 450\n\n Press any key to close",
                         any_key_closes=True)

def Object():
   # s.reset_input_buffer()
    global Str_distance
    global objects
    # Define the layout
    layout = [
        [sg.T("        Object Detector", font="any 30 bold", text_color='red', size=(0, 1))],
        [sg.T("              System", font="any 30 bold", text_color='red')],
        [sg.T(" ", size=(1, 2))],
        [sg.T("", font="any 14", key="_DISTANCE_"), sg.B('change', button_color=('dark blue', 'white'))],
        [sg.T(" ", size=(1, 2))],
        [sg.Graph(canvas_size=GRAPH_SIZE, graph_top_right=GRAPH_SIZE, graph_bottom_left=(0, 0), background_color='white', key="_GRAPH_")],
        [sg.B("Rescan!"), sg.B("Main Menu", pad=(150, 20))]
    ]



    window = sg.Window('Object Proximity Detector', layout)
    window.finalize()
    window['_DISTANCE_'].update('                    Limit Distance: ' + Str_distance + ' cm')
    graph = window["_GRAPH_"]

    outer_circle = graph.draw_arc((10, -160), (440, 360), 180, 0, style='arc', arc_color='black')
    middle_circle = graph.draw_arc((60, -110), (390, 310), 180, 0, style='arc', arc_color='black')
    inner_circle = graph.draw_arc((110, -60), (340, 260), 180, 0, style='arc', arc_color='black')
    base_line = graph.DrawLine((10, 100), (440, 100), width=2)
    while True:
        event, values = window.read(timeout=300, timeout_key="_TIMEOUT_")  # need to calculate the time between sends!
        # RX
        i=0
        info = []
        # while (s.in_waiting > 0):  # while the input buffer isn't empty
        #     enableTX = False
        #     char = s.read(size=1)  # read 1 char from the input buffer
        #     info[i] = int(char.decode("utf-8"))
        #     i = i+1
        #     # print(char.decode("ascii"))
        #     if (s.in_waiting == 0):
        #         enableTX = True  # enable transmission to echo the received data


        #  END OF RX
        if event == "_TIMEOUT_":
            for i in range(0, len(objects)):
                distance = objects[i][0]
                angle = math.radians(objects[i][1])
                print(distance * math.cos(angle)+215, distance * math.sin(angle)+100)
                graph.draw_text("X", location=(distance * math.cos(angle)+215, distance * math.sin(angle) + 100), font="any 14", color="purple")
                window["_GRAPH_"].update()
        if event in (None, "Main Menu"):
            break
        if event == "change":
            str_distance_temp = LimitChange()
            if str_distance_temp == None:
                continue
            Str_distance = str_distance_temp
            enableTX = True
            # s.reset_output_buffer()
            # while (s.out_waiting > 0 or enableTX):
            #     bytetxangle = bytes(Str_distance + '\n', 'ascii')
            #     s.write(bytetxangle)
            #     time.sleep(0.25)  # delay for accurate read/write operations on both ends
            #     if s.out_waiting == 0:
            #         enableTX = False
            window['_DISTANCE_'].update('                                Limit Distance: ' + Str_distance + ' cm')

    window.close()