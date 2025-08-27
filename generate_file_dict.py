'''
Generates a file dictionary mapping .data files to their corresponding .sdds files.
'''

import os
import sys
import re

def generate_file_dict(folder_path):
    # Extract the folder name
    folder_name = os.path.basename(folder_path)

    # Determine if the folder is HER or LER
    if "_HER_" in folder_name:
        mode = "HER"
    elif "_LER_" in folder_name:
        mode = "LER"
    else:
        print("Invalid folder name format. Expected format: ..._HER_..._YYYY_MM_DD or ..._LER_..._YYYY_MM_DD")
        return

    # Use a regular expression to find the date part (YYYY_MM_DD)
    match = re.search(r"\d{4}_\d{2}_\d{2}", folder_name)
    if not match:
        print("Invalid folder name format. Could not extract date.")
        return

    date_part = match.group(0)

    # Remove "_input_data" from the folder name if it exists
    cleaned_folder_name = folder_name.replace("input_", "")

    # Prepare the output file name
    output_file_name = f"file_dict_{cleaned_folder_name}.txt"
    output_file_path = os.path.join("./", output_file_name)

    # Collect all .data files in the folder
    file_entries = []
    for file_name in sorted(os.listdir(folder_path)):
        if file_name.endswith(".data") and f"{mode}_{date_part}" in file_name:
            full_file_path = os.path.join(folder_path, file_name)
            sdds_file_name = file_name.replace(".data", ".sdds")
            file_entries.append(f'{{"{full_file_path}", "{sdds_file_name}"}}')

    # Write to the output file
    with open(output_file_path, "w") as output_file:
        output_file.write("{\n")
        output_file.write(",\n".join(file_entries))
        output_file.write("\n}")

    print(f"File dictionary created: {output_file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_folder>")
        sys.exit(1)

    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print(f"Invalid folder path: {folder_path}")
        sys.exit(1)

    generate_file_dict(folder_path)