import json
from tkinter import Tk, Text, simpledialog, messagebox, END, INSERT, Scrollbar

class UpdateDialog(simpledialog.Dialog):
    def __init__(self, parent, title, prompt, default_text):
        self.prompt = prompt
        self.default_text = default_text
        super().__init__(parent, title)

    def body(self, master):
        self.text = Text(master, wrap="none", width=80, height=20)
        scrollbar_x = Scrollbar(master, orient="horizontal", command=self.text.xview)
        scrollbar_y = Scrollbar(master, orient="vertical", command=self.text.yview)
        self.text.configure(xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)
        self.text.insert(INSERT, self.default_text)
        self.text.grid(row=0, column=0)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")

    def apply(self):
        self.result = self.text.get("1.0", END)

    def show(self):
        self.attributes('-topmost', True)
        self.attributes('-topmost', False)
        return super().show()

def ask_yes_no(prompt, default='n'):
    while True:
        choice = input(f'{prompt} (y/n, default is {default}): ').lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        elif choice == '':
            return default == 'y'
        else:
            print('Invalid input, please enter y or n.')

def create_popup_window(title, prompt, default_text):
    root = Tk()
    root.withdraw()
    dialog = UpdateDialog(root, title, prompt, default_text)
    root.destroy()
    return dialog.result

def process_node(analysis_result, exp_config):
    exp_config_new = exp_config
    analysis_result_new = analysis_result

    while True:
        print("\nOptions:")
        print("1. Return to previous experiment")
        print("2. Repeat current experiment")
        print("3. Go to next experiment")
        choice = input("Enter your choice (1/2/3, default is 3): ")
        if choice == '' or choice == '3':
            choice = 3
            print("===== Selected: 3. Go to next experiment =====")
            if ask_yes_no("Do you want to update the analysis_results?", 'n'):
                default_text = json.dumps(analysis_result, indent=2)
                updated_text = create_popup_window("Update analysis_results", "Modify the JSON below and click OK", default_text)
                analysis_result_new = json.loads(updated_text)
                print("===== analysis_result updated: yes =====")
            else:
                analysis_result_new = analysis_result
                print("===== analysis_result updated: no =====")
        elif choice == '1':
            choice = 1
            print("===== Selected: 1. Return to previous experiment =====")
            if ask_yes_no("Do you want to update the analysis_results?", 'n'):
                default_text = json.dumps(analysis_result, indent=2)
                updated_text = create_popup_window("Update analysis_results", "Modify the JSON below and click OK", default_text)
                analysis_result_new = json.loads(updated_text)
                print("===== analysis_result updated: yes =====")
            else:
                analysis_result_new = analysis_result
                print("===== analysis_result updated: no =====")
        elif choice == '2':
            choice = 2
            print("===== Selected: 2. Repeat current experiment =====")
            if ask_yes_no("Do you want to update the exp_config?", 'n'):
                default_text = json.dumps(exp_config, indent=2)
                updated_text = create_popup_window("Update exp_config", "Modify the JSON below and click OK", default_text)
                exp_config_new = json.loads(updated_text)
                print("===== exp_config updated: yes =====")
            else:
                exp_config_new = exp_config
                print("===== exp_config updated: no =====")
        else:
            print("Invalid choice. Please enter a valid choice.")
            continue
        break

    return choice, exp_config_new, analysis_result_new
