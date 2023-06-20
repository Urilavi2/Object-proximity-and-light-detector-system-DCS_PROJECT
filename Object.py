import PySimpleGUI as sg
import serial as ser
import time

Str_distance = '450'

# s = ser.Serial('COM3', baudrate=9600, bytesize=ser.EIGHTBITS,
#                    parity=ser.PARITY_NONE, stopbits=ser.STOPBITS_ONE,
#                    timeout=1)   # timeout of 1 sec so that the read and write operations are blocking,
#                                 # when the timeout expires the program will continue
#
#     # CHANGE THE COM!!


enableTX = True

GRAPH_SIZE = (600, 400)


class ObjectX:
    def __int__(self, icon, info):
        self.icon = "X"
        self.info = {"distance": 999, "angle": 999}

    def set_info(self, new_dis, new_ang):
        self.info["distance"] = new_dis
        self.info["angle"] = new_ang

    def get_info(self):
        return self.info

    def get_icon(self):
        return self.icon

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
                sg.popup("Distance must be: \n\n- AN INTEGER!\n\n- bigger then 0\n- smaller then 450\n\n Press any key to close",
                         any_key_closes=True)

def Object():

    global Str_distance
    global objects
    # Define the layout
    layout = [
        [sg.T("              Object Detector", font="any 30 bold", text_color='red', size=(0,1))],
        [sg.T("                    System", font="any 30 bold", text_color='red')],
        [sg.T(" ", size=(1,2))],
        [sg.T("", font="any 14", key="_DISTANCE_"), sg.B('change', button_color=('dark blue', 'white'))],
        [sg.T(" ", size=(1, 2))],
        [sg.Graph(canvas_size=GRAPH_SIZE, graph_top_right=GRAPH_SIZE, graph_bottom_left=(0,0), background_color='white', key="_GRAPH_")],
        [sg.B("Main Menu", pad=(250, 20))]
    ]



    window = sg.Window('Object Proximity Detector', layout)
    window.finalize()
    window['_DISTANCE_'].update('                                Limit Distance: ' + Str_distance + ' cm')
    graph = window["_GRAPH_"]

    outer_circle = graph.draw_arc((10,-300), (590,390), 180, 0, style='arc', arc_color='black')
    middle_circle = graph.draw_arc((100, -210), (500, 300), 180, 0, style='arc', arc_color='black')
    inner_circle = graph.draw_arc((190, -120), (420, 210), 180, 0, style='arc', arc_color='black')
    base_line = graph.DrawLine((10,45),(590,45), width=2)
    base_lin2e = graph.DrawLine((10,6),(11,6), width=2)


    while True:
        event, values = window.read()
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