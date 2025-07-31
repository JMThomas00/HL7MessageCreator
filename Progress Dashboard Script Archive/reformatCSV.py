import pandas as pd
import os

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# List of CSV files to reformat
csv_files = ["patient_names.csv", "staff_names.csv", "surgeon_names.csv"]

for csv_file in csv_files:
    # Construct the full path to the CSV file
    csv_path = os.path.join(SCRIPT_DIR, csv_file)
    
    # Check if the file exists
    if not os.path.exists(csv_path):
        print(f"Error: Could not find '{csv_file}' at '{csv_path}'. Please ensure the file exists in the same directory as this script.")
        continue
    
    try:
        # Read the CSV
        print(f"Processing {csv_file}...")
        df = pd.read_csv(csv_path)
        
        # Verify the expected column exists
        if "First Name,Last Name" not in df.columns:
            print(f"Error: '{csv_file}' does not have a 'First Name,Last Name' column. Found columns: {list(df.columns)}")
            continue
        
        # Split the 'First Name,Last Name' column into two columns
        df[["first_name", "last_name"]] = df["First Name,Last Name"].str.split(",", expand=True)
        
        # Drop the original column
        df = df.drop(columns=["First Name,Last Name"])
        
        # Save the updated CSV
        df.to_csv(csv_path, index=False)
        print(f"Successfully reformatted {csv_file}")
    
    except Exception as e:
        print(f"Error processing {csv_file}: {str(e)}")