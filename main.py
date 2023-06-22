import PySimpleGUI as sg
import Telemeter
import script
import serial as ser
import time
import Object

s = ser.Serial('COM3', baudrate=9600, bytesize=ser.EIGHTBITS,
               parity=ser.PARITY_NONE, stopbits=ser.STOPBITS_ONE,
               timeout=1)  # timeout of 1 sec so that the read and write operations are blocking,

# when the timeout expires the program will continue

# CHANGE THE COM!!

enableTX = True


def sendstate(state):
    s.reset_output_buffer()
    while (s.out_waiting > 0 or enableTX):
        bytetxstate = bytes(state + '\n', 'ascii')
        s.write(bytetxstate)
        if s.out_waiting == 0:
            enableTX = False


def main():
    global enableTX
    layout = [[sg.T("DCS - Final Project", font="any 30 italic underline", pad=(249, 10), text_color='red')],
              [sg.T("     Light Source and Object proximity\n                   detector system", font="any 34 bold",
                    text_color='blue')],
              [sg.B("Object\nDetector\nSystem", key="_OBJECT_", size=(10, 5), button_color=("white", "red"),
                    pad=(100, 70)),
               sg.B("Telemeter", key="_TELEMETER_", size=(10, 5), button_color=("white", "red"), pad=(90, 70)),
               sg.B("Light Source\nand Object\nDetector", key="_OBJECT&LIGHT_", size=(10, 5),
                    button_color=("white", "red"), pad=(104, 70))],
              [sg.B("Light Source\nDetector\nSystem", key="_LIGHT_", size=(10, 5), button_color=("white", "red"),
                    pad=(205, 5)),
               sg.B("Script\nMode", key="_SCRIPT_", size=(10, 5), button_color=("white", "red"), pad=(25, 5))],
              [sg.B("Exit", key="_EXIT_", size=(10, 2), pad=(370, 50))]]

    window = sg.Window("Light Source and Object proximity", layout, location=(500, 100), size=(900, 700))

    while True:
        event, values = window.read()
        if event in (None, "_EXIT_"):
            sg.popup("goodbye!", auto_close=True, auto_close_duration=0.5)
            break
        if event == "_OBJECT_":  # state 1
            window.hide()
            sendstate('1')
            Object.Object()
            enableTX = True
            window.un_hide()
        if event == "_TELEMETER_":  # state 2
            window.hide()
            angle = Telemeter.AngleChange()
            if angle:
                sendstate('2')
                sendstate(angle)  # first time the angle is sent!
                Telemeter.Telemeter(angle)
                enableTX = True
            window.un_hide()
        if event == "_SCRIPT_":  # state 5
            window.hide()
            sendstate('5')
            script.ScriptMenu()
            enableTX = True
            window.un_hide()
        if event == "_OBJECT&LIGHT_":  # state 4
            pass
        if event == "_LIGHT_":  # state 3
            pass
    window.close()


if __name__ == '__main__':
    main()

