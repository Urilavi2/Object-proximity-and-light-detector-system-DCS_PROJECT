import PySimpleGUI as sg
import serial as ser
import time


def AngleChange():
    layout = [[sg.T('Wanted angle: '), sg.I(key='_INPUT_')],
              [sg.B('Ok'), sg.B('Cancel')]]
    window = sg.Window('AngleUpdater', layout)
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):
            window.close()
            return None
        if event == 'Ok':
            try:
                new_angle = int(values['_INPUT_'])
                if new_angle < 0 or new_angle > 180:
                    sg.popup("angle must be: \n\n- bigger then 0\n- smaller then 180\n\n Press any key to close",
                             any_key_closes=True)
                    continue
                window.close()
                return values['_INPUT_']
            except Exception:
                sg.popup("angle must be: \n\n- AN INTEGER!\n\n- bigger then 0\n- smaller then 180\n\n Press any key to close",
                         any_key_closes=True)



def Telemeter(angle):
    layout = [[sg.T('    ', font="any 34 bold "),
               sg.T('Telemeter', font="any 34 bold underline", text_color='red', pad=(120, 10))],

              [sg.T('', key='_ANGLE_', pad=(100, 10), font='any 14'),
               sg.B('change', button_color=('dark blue', 'white'))],
              [sg.T('', key='_DISTANCE_', pad=(100, 10), font='any 14')],
              [sg.B("Main Menu", pad=(250, 20))]
              ]

    s = ser.Serial('COM3', baudrate=9600, bytesize=ser.EIGHTBITS,
                   parity=ser.PARITY_NONE, stopbits=ser.STOPBITS_ONE,
                   timeout=1)   # timeout of 1 sec so that the read and write operations are blocking,
                                # when the timeout expires the program will continue

    # CHANGE THE COM!!


    enableTX = True
    str_angle = str(angle)
    str_distance = '0'
    window = sg.Window('Telemeter', layout, size=(600, 250))
    window.finalize()
    window['_ANGLE_'].update('Known angle: ' + str_angle + '°')
    window['_DISTANCE_'].update('Distance: ' + str_distance + ' cm')

    while True:
        event, values = window.read()
        if event in (None, "Main Menu"):
            break
        if s.in_waiting > 0:
            s.reset_input_buffer()
            while (s.in_waiting > 0):
                charByte = s.read(size=1)
                time.sleep(0.25)                        # delay for accurate read/write operations on both ends
                str_distance = charByte.decode("ascii")
                if s.in_waiting == 0:
                    enableTX = True
                window['_DISTANCE_'].update('Distance: ' + str_distance + ' cm')
        if event == 'change':
            str_angle_temp = AngleChange()
            if (str_angle_temp == None):
                continue
            str_angle = str_angle_temp
            s.reset_output_buffer()
            while (s.out_waiting > 0 or enableTX):
                bytetxangle = bytes(str_angle + '\n', 'ascii')
                s.write(bytetxangle)
                time.sleep(0.25)                        # delay for accurate read/write operations on both ends
                if s.out_waiting == 0:
                   enableTX = False
            window['_ANGLE_'].update('Known angle: ' + str_angle + '°')
    window.close()