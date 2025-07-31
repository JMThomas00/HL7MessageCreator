import tkinter as tk
from tkinter import scrolledtext
import csv
import os
import random
import re

# Define color scheme
BG_COLOR = "#1F2139"  # rgb(31, 33, 57)
TEXT_COLOR = "#FFFFFF"  # rgb(255, 255, 255)
PREVIEW_BG = "#1E1E1E"  # rgb(30, 30, 30)
TITLE_HL7_MSG = "#465BE7"  # rgb(70, 91, 231)
TITLE_EDITOR = "#7DCAE3"  # rgb(125, 202, 227)
DITHERED_TEXT = "#808080"  # Gray for unedited fields and disabled buttons

# Get the directory of the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load names from CSV files
def load_names(file_name):
    """Load names from a CSV file, skipping the header."""
    file_path = os.path.join(SCRIPT_DIR, file_name)
    try:
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            return [(row[0].strip(), row[1].strip()) for row in reader]
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find {file_name} in {SCRIPT_DIR}")
    except Exception as e:
        raise Exception(f"Failed to read {file_name}: {str(e)}")

# Group files into patient blocks
def get_patient_blocks(folders):
    """Group HL7 files into patient blocks based on patient name prefix."""
    patient_blocks = []
    for folder in folders:
        folder_path = os.path.join(SCRIPT_DIR, folder)
        if not os.path.exists(folder_path):
            continue
        files = [f for f in os.listdir(folder_path) if f.endswith(".hl7")]
        patient_groups = {}
        for file in files:
            patient_name = file.split('-')[0] if '-' in file else file.replace(".hl7", "")
            if patient_name not in patient_groups:
                patient_groups[patient_name] = []
            patient_groups[patient_name].append(os.path.join(folder_path, file))
        for patient_name, patient_files in patient_groups.items():
            patient_files.sort()
            patient_blocks.append((folder, patient_name, patient_files))
    return sorted(patient_blocks, key=lambda x: (x[0], x[1]))

# Replace variables in a message
def replace_variables(message, primary_fname, primary_lname, staff_names, manual_values=None):
    """Replace name variables in a message."""
    if manual_values:
        temp_message = message
        for (var, instance), value in manual_values.items():
            if instance:  # Context-specific (e.g., AIP|2)
                lines = temp_message.split('\n')
                for i, line in enumerate(lines):
                    if instance in line and var in line:
                        lines[i] = lines[i].replace(var, value, 1)
                temp_message = '\n'.join(lines)
            else:
                temp_message = temp_message.replace(var, value)
        return temp_message
    
    # Random replacement
    message = message.replace("{primaryFirstName}", primary_fname)
    message = message.replace("{primaryLastName}", primary_lname)
    
    def replace_staff(match):
        var = match.group(1)
        if var == "firstName":
            return random.choice(staff_names)[0]
        elif var == "lastName":
            return random.choice(staff_names)[1]
        return match.group(0)
    
    return re.sub(r"\{(firstName|lastName)\}", replace_staff, message)

# Find variable instances in a message
def find_variable_instances(message):
    """Identify unique variable instances (e.g., PV1 {primaryLastName}, AIP|2 {lastName})."""
    instances = []
    lines = message.split('\n')
    for line in lines:
        if '{primaryLastName}' in line or '{primaryFirstName}' in line:
            if line.startswith('PV1'):
                if '{primaryLastName}' in line:
                    instances.append(('PV1', '{primaryLastName}'))
                if '{primaryFirstName}' in line:
                    instances.append(('PV1', '{primaryFirstName}'))
            elif line.startswith('AIP'):
                seq = line.split('|')[1]
                if '{primaryLastName}' in line:
                    instances.append((f'AIP|{seq}', '{primaryLastName}'))
                if '{primaryFirstName}' in line:
                    instances.append((f'AIP|{seq}', '{primaryFirstName}'))
        if '{lastName}' in line or '{firstName}' in line:
            if line.startswith('AIP'):
                seq = line.split('|')[1]
                if '{lastName}' in line:
                    instances.append((f'AIP|{seq}', '{lastName}'))
                if '{firstName}' in line:
                    instances.append((f'AIP|{seq}', '{firstName}'))
    return sorted(set(instances), key=lambda x: x[0])

# Main application class
class HL7MessageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("HL7 Message Editor")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(800, 600)
        
        # Load names
        try:
            self.surgeon_names = load_names("surgeon_names.csv")
            self.staff_names = load_names("names.csv")
        except Exception as e:
            tk.Label(self.root, text=str(e), fg="red", bg=BG_COLOR).pack(pady=10)
            self.root.after(2000, self.root.quit)
            return
        
        # Title (centered)
        title_container = tk.Frame(self.root, bg=BG_COLOR)
        title_container.pack(pady=10)
        title_frame = tk.Frame(title_container, bg=BG_COLOR)
        title_frame.pack()
        tk.Label(title_frame, text="HL7 Message", font=("Georgia", 32), fg=TITLE_HL7_MSG, bg=BG_COLOR).pack(side=tk.LEFT)
        tk.Label(title_frame, text=" Editor", font=("Georgia", 32), fg=TITLE_EDITOR, bg=BG_COLOR).pack(side=tk.LEFT)
        
        # Main content frame
        self.content_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Preview text box
        self.preview_text = scrolledtext.ScrolledText(self.content_frame, width=80, height=20, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Button frame (centered)
        self.button_container = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.button_container.pack(fill=tk.X)
        self.button_frame = tk.Frame(self.button_container, bg=BG_COLOR)
        self.button_frame.pack(pady=5)
        
        # Navigation buttons
        self.prev_button = tk.Button(self.button_frame, text="Previous", command=self.prev_block, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A")
        self.prev_button.pack(side=tk.LEFT, padx=5)
        self.next_button = tk.Button(self.button_frame, text="Next", command=self.next_block, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A")
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # Command buttons
        tk.Button(self.button_frame, text="Randomize All", command=self.randomize_all, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Quit", command=self.quit, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Save and Exit", command=self.save_and_exit, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)
        
        # Prompt frame
        self.prompt_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.prompt_frame.pack(fill=tk.X, pady=5)
        
        # Edit fields frame
        self.edit_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.edit_frame.pack(fill=tk.X, pady=5, anchor='w')
        
        # Initialize state
        self.folders = ["CurrentDay", "NextDay", "PreviousDay"]
        self.current_block = -1
        self.patient_blocks = []
        self.edited_messages = {}
        self.manual_entries = {}
        self.edit_fields = []
        self.load_blocks()
        self.next_block()

    def load_blocks(self):
        """Load all patient blocks."""
        self.patient_blocks = get_patient_blocks(self.folders)
        if not self.patient_blocks:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, "No HL7 files found in CurrentDay, NextDay, or PreviousDay.\n")
    
    def update_button_states(self):
        """Update Previous and Next button states based on current_block."""
        if self.current_block <= 0:
            self.prev_button.config(state="disabled", fg=DITHERED_TEXT)
        else:
            self.prev_button.config(state="normal", fg=TEXT_COLOR)
        if self.current_block >= len(self.patient_blocks) - 1:
            self.next_button.config(state="disabled", fg=DITHERED_TEXT)
        else:
            self.next_button.config(state="normal", fg=TEXT_COLOR)
    
    def show_prompt(self, message, options, callback):
        """Show a prompt with buttons in the prompt frame."""
        for widget in self.prompt_frame.winfo_children():
            widget.destroy()
        tk.Label(self.prompt_frame, text=message, fg=TEXT_COLOR, bg=BG_COLOR).pack(side=tk.LEFT, padx=5)
        for option in options:
            tk.Button(self.prompt_frame, text=option, command=lambda o=option: callback(o),
                      bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)
    
    def clear_edit_fields(self):
        """Remove all manual edit fields."""
        for widget in self.edit_frame.winfo_children():
            widget.destroy()
        self.edit_fields = []
        self.manual_entries = {}
    
    def highlight_variable(self, instance, var, message):
        """Highlight a variable in the preview text."""
        self.preview_text.tag_remove("highlight", "1.0", tk.END)
        if not message:
            return
        lines = message.split('\n')
        for line in lines:
            if instance in line and var in line:
                start_idx = line.find(var)
                if start_idx != -1:
                    line_num = lines.index(line) + 1
                    start_pos = f"{line_num}.{start_idx}"
                    end_pos = f"{line_num}.{start_idx + len(var)}"
                    self.preview_text.tag_add("highlight", start_pos, end_pos)
                    self.preview_text.tag_config("highlight", background="yellow", foreground="black")
                    break
    
    def update_preview(self):
        """Update the preview with the current block’s first message."""
        if 0 <= self.current_block < len(self.patient_blocks):
            folder, patient, block_files = self.patient_blocks[self.current_block]
            with open(block_files[0], 'r') as file:
                message = file.read()
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, message)
            self.show_prompt(f"Edit patient block ({patient})?", ["Yes", "No"], self.handle_edit_prompt)
        else:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, "No more patient blocks.\n")
            for widget in self.prompt_frame.winfo_children():
                widget.destroy()
        self.update_button_states()
    
    def handle_edit_prompt(self, choice):
        """Handle the edit block prompt."""
        if choice == "Yes":
            self.show_prompt("Randomize or manually edit?", ["Random", "Manual"], self.handle_mode_choice)
        else:
            self.next_block()
    
    def handle_mode_choice(self, choice):
        """Handle the random/manual choice."""
        if choice == "Random":
            self.randomize_block()
        else:
            self.manual_edit_block()
    
    def prev_block(self):
        """Go to the previous patient block."""
        if self.current_block > 0:
            self.current_block -= 1
            self.clear_edit_fields()
            self.update_preview()
    
    def next_block(self):
        """Go to the next patient block."""
        if self.current_block < len(self.patient_blocks) - 1:
            self.current_block += 1
            self.clear_edit_fields()
            self.update_preview()
    
    def randomize_all(self):
        """Randomize names for all patient blocks with confirmation."""
        self.show_prompt("This will randomize all names for all messages. Proceed?", ["Yes", "No"], self.handle_randomize_all)
    
    def handle_randomize_all(self, choice):
        """Handle randomize all confirmation."""
        if choice == "Yes":
            self.edited_messages = {}
            total_messages = 0
            total_patients = len(self.patient_blocks)
            for folder, patient, block_files in self.patient_blocks:
                primary_fname, primary_lname = random.choice(self.surgeon_names)
                for file_path in block_files:
                    with open(file_path, 'r') as file:
                        message = file.read()
                    self.edited_messages[file_path] = replace_variables(message, primary_fname, primary_lname, self.staff_names)
                    total_messages += 1
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, "Randomization complete.\n")
            self.show_prompt(f"{total_messages} messages for {total_patients} patients were edited.", ["OK"], lambda x: self.update_preview())
        else:
            self.update_preview()
    
    def randomize_block(self):
        """Randomize names for the current block."""
        if 0 <= self.current_block < len(self.patient_blocks):
            folder, patient, block_files = self.patient_blocks[self.current_block]
            primary_fname, primary_lname = random.choice(self.surgeon_names)
            edited = {}
            for file_path in block_files:
                with open(file_path, 'r') as file:
                    message = file.read()
                edited[file_path] = replace_variables(message, primary_fname, primary_lname, self.staff_names)
            self.edited_messages.update(edited)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, edited[block_files[0]])
            self.show_prompt("Save and proceed, reroll, or edit manually?", ["Save", "Reroll", "Manual"], self.handle_post_edit)
    
    def manual_edit_block(self):
        """Create fields for manual editing of each variable instance."""
        if 0 <= self.current_block < len(self.patient_blocks):
            folder, patient, block_files = self.patient_blocks[self.current_block]
            with open(block_files[0], 'r') as file:
                message = file.read()
            instances = find_variable_instances(message)
            self.clear_edit_fields()
            
            for instance, var in instances:
                frame = tk.Frame(self.edit_frame, bg=PREVIEW_BG)
                frame.pack(fill=tk.X, pady=2, anchor='w')
                tk.Label(frame, text=f"{instance}", fg=TEXT_COLOR, bg=PREVIEW_BG, width=10).pack(side=tk.LEFT, padx=5)
                entry = tk.Entry(frame, bg=PREVIEW_BG, fg=DITHERED_TEXT, insertbackground=TEXT_COLOR)
                entry.insert(0, var)
                entry.bind("<FocusIn>", lambda e, i=instance, v=var: self.on_entry_focus(e, i, v, entry))
                entry.bind("<KeyRelease>", lambda e, i=instance, v=var, fp=block_files[0]: self.on_entry_change(e, i, v, entry, fp))
                entry.pack(side=tk.LEFT, padx=5)
                self.edit_fields.append((entry, instance, var))
            
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, message)
            self.show_prompt("Apply manual edits?", ["Apply", "Cancel"], self.handle_manual_apply)
    
    def on_entry_focus(self, event, instance, var, entry):
        """Handle entry focus: clear dithered text and highlight variable."""
        if entry.get() == var:
            entry.delete(0, tk.END)
            entry.config(fg=TEXT_COLOR)
        message = self.preview_text.get("1.0", tk.END).strip()
        self.highlight_variable(instance, var, message)
    
    def on_entry_change(self, event, instance, var, entry, file_path):
        """Update manual entries and preview when typing."""
        value = entry.get()
        self.manual_entries[(var, instance)] = value if value else var
        with open(file_path, 'r') as file:
            message = file.read()
        updated_message = replace_variables(message, "", "", self.staff_names, self.manual_entries)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, updated_message)
        self.highlight_variable(instance, var, updated_message)
    
    def handle_manual_apply(self, choice):
        """Apply or cancel manual edits."""
        if choice == "Apply" and 0 <= self.current_block < len(self.patient_blocks):
            folder, patient, block_files = self.patient_blocks[self.current_block]
            edited = {}
            for file_path in block_files:
                with open(file_path, 'r') as file:
                    message = file.read()
                edited[file_path] = replace_variables(message, "", "", self.staff_names, self.manual_entries)
            self.edited_messages.update(edited)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, edited[block_files[0]])
            self.clear_edit_fields()
            self.show_prompt("Save and proceed, reroll, or edit manually?", ["Save", "Reroll", "Manual"], self.handle_post_edit)
        else:
            self.clear_edit_fields()
            self.update_preview()
    
    def handle_post_edit(self, choice):
        """Handle post-edit actions."""
        if choice == "Save":
            self.next_block()
        elif choice == "Reroll":
            self.randomize_block()
        elif choice == "Manual":
            self.manual_edit_block()
    
    def quit(self):
        """Prompt to confirm quit."""
        self.show_prompt("Changes will not be saved. Are you sure you want to quit?", ["Yes", "No"], self.handle_quit)
    
    def handle_quit(self, choice):
        """Handle quit confirmation."""
        if choice == "Yes":
            self.root.quit()
        else:
            self.update_preview()
    
    def save_and_exit(self):
        """Save changes and exit."""
        for file_path, message in self.edited_messages.items():
            with open(file_path, 'w') as file:
                file.write(message)
        self.root.quit()

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = HL7MessageEditor(root)
    root.mainloop()