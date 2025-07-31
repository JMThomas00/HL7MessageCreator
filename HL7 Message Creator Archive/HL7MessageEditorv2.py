import os
import tkinter as tk
from tkinter import filedialog, messagebox
import random
import csv
import shutil

# Constants
BG_COLOR = "#1f2139"
WHITE = "#FFFFFF"
ERROR_COLOR = "#FF5733"

# Load names from CSV
def load_names(file_path):
    try:
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            return list(reader)
    except Exception as e:
        raise Exception(f"Error loading names from {file_path}: {e}")

# Get patient blocks from folder
def get_patient_blocks(folders):
    patient_blocks = []
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for filename in os.listdir(folder):
            if filename.endswith(".hl7"):
                with open(os.path.join(folder, filename), 'r') as f:
                    content = f.read()
                    patient_blocks.append(content)
    return patient_blocks

# Generate random time for case event durations
def generate_random_duration(min_duration=90, max_duration=180, variance=15):
    return random.randint(min_duration, max_duration) + random.randint(-variance, variance)

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
        
        # Initialize state (unchanged)
        self.folders = ["CurrentDay", "NextDay", "PreviousDay"]
        self.current_block = -1
        self.patient_blocks = []
        self.edited_messages = {}
        self.manual_entries = {}
        self.load_blocks()  # Now calling load_blocks
        self.next_block()

    def load_blocks(self):
        """Load patient blocks from HL7 files in the specified folders."""
        try:
            self.patient_blocks = get_patient_blocks(self.folders)
        except Exception as e:
            self.show_error(f"Failed to load patient blocks: {str(e)}")
        
    def next_block(self):
        """Move to the next patient block."""
        self.current_block += 1
        if self.current_block < len(self.patient_blocks):
            self.load_message(self.patient_blocks[self.current_block])
        else:
            self.show_error("No more patient blocks available.")

    def load_message(self, message):
        """Load a specific HL7 message into the editor."""
        self.current_message = message
        self.display_message()

    def display_message(self):
        """Display the current HL7 message in the GUI."""
        # For now, just display the message in a text box
        text_box = tk.Text(self.root, bg=BG_COLOR, fg=WHITE, wrap=tk.WORD)
        text_box.insert(tk.END, self.current_message)
        text_box.pack(pady=10)

    def show_error(self, message):
        """Show an error message in a popup."""
        messagebox.showerror("Error", message)

    def save_message(self, message):
        """Save the edited HL7 message to a file."""
        try:
            filename = f"edited_message_{random.randint(1000, 9999)}.hl7"
            with open(filename, 'w') as f:
                f.write(message)
            messagebox.showinfo("Success", f"Message saved as {filename}")
        except Exception as e:
            self.show_error(f"Error saving message: {e}")

    def update_patient_data(self):
        """Update patient data with new values."""
        pass  # Implement your logic here if needed for updating the patient data

# Setup the Tkinter root window
root = tk.Tk()
app = HL7MessageEditor(root)
root.mainloop()
