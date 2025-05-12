import PySimpleGUI as sg                      # Part 1 - The import

def gui_confirm(text="Continue?"):
    # Define the window's contents
    layout = [  [sg.Text(text)],     # Part 2 - The Layout
                [sg.Button('Yes'), sg.Button('No')] ]

    # Create the window
    window = sg.Window('Confirm', layout)      # Part 3 - Window Defintion
                                                    
    # Display and interact with the Window
    event, values = window.read()                   # Part 4 - Event loop or Window.read call

    # Finish up by removing from the screen
    window.close()                                  # Part 5 - Close the Window
    print(event)
    return event == "Yes"


