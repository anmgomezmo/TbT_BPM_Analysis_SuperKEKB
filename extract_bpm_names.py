'''
Extraction of BPM names from various file formats:
    - .data files
    - .sdds files
    - .ampsx files
    - .freqsx files

Creates a comprehensive list of all BPM names found across these files. 
Additional colormaps can be created based on the presence or absence of BPMs in these files.
'''

import re
import os
from glob import glob
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import json

# Set date variable (e.g., "HER_2024_06_17")
date = "HER_2024_03_14"  # Change this to the desired date string
folder = "HER_V_kick_2024_03_14"  # Change this to the desired folder name
typed = "unsynched"

# Define directories
data_dir = f"/home/andym/Documents/SOMA/SOMA/input/input_{folder}"
sdds_dir = f"/home/andym/Documents/SOMA/SOMA/output/output_{folder}/{typed}_sdds"
harmonic_dir = f"/home/andym/Documents/SOMA/SOMA/output/output_{folder}/{typed}_harmonic"
output_dir = f"/home/andym/Documents/SOMA/SOMA/output/output_{folder}"  
os.makedirs(output_dir, exist_ok=True)

# Find all .data files
data_files = sorted(glob(os.path.join(data_dir, "*.data")))

# Prepare lists for plotting
times = []
lost_data_sdds = []
lost_sdds_ampsx = []
lost_sdds_freqsx = []

# For colormaps
all_bpm_names = set()
bpm_presence_matrix = []

for datafile in data_files:
    base = os.path.basename(datafile)
    parts = base.replace('.data', '').split('_')
    time = "_".join(parts[-3:])  # e.g., "17_37_09"
    times.append(time)

    sddsfile = os.path.join(sdds_dir, f"{date}_{time}.sdds")
    ampsxfile = os.path.join(harmonic_dir, f"{date}_{time}.sdds.ampsx")
    freqsxfile = os.path.join(harmonic_dir, f"{date}_{time}.sdds.freqsx")

    if not (os.path.exists(sddsfile) and os.path.exists(ampsxfile) and os.path.exists(freqsxfile)):
        print(f"Skipping {base}: corresponding files not found.")
        lost_data_sdds.append(None)
        lost_sdds_ampsx.append(None)
        lost_sdds_freqsx.append(None)
        continue

    # Extract BPMs from .data file
    with open(datafile, "r") as f:
        data = f.read()
    bpm_names_data = set(re.findall(r'"([^"]+)"->', data))
    all_bpm_names.update(bpm_names_data)
    bpm_presence_matrix.append([1 if bpm in bpm_names_data else 0 for bpm in sorted(bpm_names_data)])

    # Extract BPMs from .sdds file
    bpm_names_sdds = set()
    with open(sddsfile, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            match = re.match(r'\s*\d+\s+(\S+)', line)
            if match:
                bpm_names_sdds.add(match.group(1))

    # Extract BPMs from .ampsx file
    bpm_names_ampsx = set()
    with open(ampsxfile, "r") as f:
        for line in f:
            if line.startswith("*"):
                bpm_names_ampsx = set(line.split()[1:])
                break

    # Extract BPMs from .freqsx file
    bpm_names_freqsx = set()
    with open(freqsxfile, "r") as f:
        for line in f:
            if line.startswith("*"):
                bpm_names_freqsx = set(line.split()[1:])
                break

    # Compare and collect results
    disappeared_data_sdds = bpm_names_data - bpm_names_sdds
    disappeared_sdds_ampsx = bpm_names_sdds - bpm_names_ampsx
    disappeared_sdds_freqsx = bpm_names_sdds - bpm_names_freqsx

    lost_data_sdds.append(len(disappeared_data_sdds))
    lost_sdds_ampsx.append(len(disappeared_sdds_ampsx))
    lost_sdds_freqsx.append(len(disappeared_sdds_freqsx))

# Finalize BPM columns for colormaps
all_bpm_names = sorted(all_bpm_names)
bpm_columns = all_bpm_names

# --- Colormap for BPM presence in .data files (all times) ---
bpm_presence_matrix = []
for datafile in data_files:
    with open(datafile, "r") as f:
        data = f.read()
    bpm_names = set(re.findall(r'"([^"]+)"->', data))
    row = [1 if bpm in bpm_names else 0 for bpm in bpm_columns]
    bpm_presence_matrix.append(row)

# --- Colormap for BPM presence in .sdds files (all times) ---
sdds_files = sorted(glob(os.path.join(sdds_dir, "*.sdds")))
sdds_times = []
sdds_presence_matrix = []

for sddsfile in sdds_files:
    base = os.path.basename(sddsfile)
    parts = base.replace('.sdds', '').split('_')
    time = "_".join(parts[-3:])
    sdds_times.append(time)

    bpm_names_sdds = set()
    with open(sddsfile, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            match = re.match(r'\s*\d+\s+(\S+)', line)
            if match:
                bpm_names_sdds.add(match.group(1))
    row = [1 if bpm in bpm_names_sdds else 0 for bpm in bpm_columns]
    sdds_presence_matrix.append(row)

# --- Colormap for BPM presence in .ampsx files (all times) ---
ampsx_files = sorted(glob(os.path.join(harmonic_dir, "*.sdds.ampsx")))
ampsx_times = []
ampsx_presence_matrix = []

for ampsxfile in ampsx_files:
    base = os.path.basename(ampsxfile)
    parts = base.replace('.sdds.ampsx', '').split('_')
    time = "_".join(parts[-3:])
    ampsx_times.append(time)

    bpm_names_ampsx = set()
    with open(ampsxfile, "r") as f:
        for line in f:
            if line.startswith("*"):
                bpm_names_ampsx = set(line.split()[1:])
                break
    row = [1 if bpm in bpm_names_ampsx else 0 for bpm in bpm_columns]
    ampsx_presence_matrix.append(row)

# --- Colormap for BPM presence in .freqsx files (all times) ---
freqsx_files = sorted(glob(os.path.join(harmonic_dir, "*.sdds.freqsx")))
freqsx_times = []
freqsx_presence_matrix = []

for freqsxfile in freqsx_files:
    base = os.path.basename(freqsxfile)
    parts = base.replace('.sdds.freqsx', '').split('_')
    time = "_".join(parts[-3:])
    freqsx_times.append(time)

    bpm_names_freqsx = set()
    with open(freqsxfile, "r") as f:
        for line in f:
            if line.startswith("*"):
                bpm_names_freqsx = set(line.split()[1:])
                break
    row = [1 if bpm in bpm_names_freqsx else 0 for bpm in bpm_columns]
    freqsx_presence_matrix.append(row)

# --- Save all plots in a single PDF ---
with PdfPages(os.path.join(output_dir, f"bpm_presence_{typed}.pdf")) as pdf:
    # Plotting lost BPMs transitions
    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(times))
    ax.plot([t for i, t in enumerate(times) if lost_data_sdds[i] is not None],
            [v for v in lost_data_sdds if v is not None],
            label='.data → .sdds', marker='o', color='tab:blue')
    ax.plot([t for i, t in enumerate(times) if lost_sdds_ampsx[i] is not None],
            [v for v in lost_sdds_ampsx if v is not None],
            label='.sdds → .ampsx', marker='s', color='tab:orange')
    ax.plot([t for i, t in enumerate(times) if lost_sdds_freqsx[i] is not None],
            [v for v in lost_sdds_freqsx if v is not None],
            label='.sdds → .freqsx', marker='^', color='tab:green')
    ax.set_xlabel('Time', fontsize=14)
    ax.set_ylabel('Number of BPMs lost', fontsize=14)
    ax.set_title(f'BPMs lost during file transitions ({date})', fontsize=16)
    ax.legend(fontsize=12)
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

    # Colormap for .data files
    fig, ax = plt.subplots(figsize=(max(12, len(bpm_columns)//3), max(8, len(data_files)//4)))
    im = ax.imshow(np.array(bpm_presence_matrix), aspect='auto', cmap='plasma', vmin=0, vmax=1)
    ax.set_xlabel('BPM Name', fontsize=14)
    ax.set_ylabel('File (Time)', fontsize=14)
    ax.set_title(f'BPM presence in .data files ({date})', fontsize=16)
    ax.set_xticks(np.arange(len(bpm_columns)))
    ax.set_xticklabels(bpm_columns, rotation=90, fontsize=7)
    ax.set_yticks(np.arange(len(times)))
    ax.set_yticklabels(times, fontsize=8)
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

    # Colormap for .sdds files
    fig, ax = plt.subplots(figsize=(max(12, len(bpm_columns)//3), max(8, len(sdds_files)//4)))
    im = ax.imshow(np.array(sdds_presence_matrix), aspect='auto', cmap='plasma', vmin=0, vmax=1)
    ax.set_xlabel('BPM Name', fontsize=14)
    ax.set_ylabel('File (Time)', fontsize=14)
    ax.set_title(f'BPM presence in .sdds files ({date})', fontsize=16)
    ax.set_xticks(np.arange(len(bpm_columns)))
    ax.set_xticklabels(bpm_columns, rotation=90, fontsize=7)
    ax.set_yticks(np.arange(len(sdds_times)))
    ax.set_yticklabels(sdds_times, fontsize=8)
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

    # Colormap for .ampsx files
    fig, ax = plt.subplots(figsize=(max(12, len(bpm_columns)//3), max(8, len(ampsx_files)//4)))
    im = ax.imshow(np.array(ampsx_presence_matrix), aspect='auto', cmap='plasma', vmin=0, vmax=1)
    ax.set_xlabel('BPM Name', fontsize=14)
    ax.set_ylabel('File (Time)', fontsize=14)
    ax.set_title(f'BPM presence in .ampsx files ({date})', fontsize=16)
    ax.set_xticks(np.arange(len(bpm_columns)))
    ax.set_xticklabels(bpm_columns, rotation=90, fontsize=7)
    ax.set_yticks(np.arange(len(ampsx_times)))
    ax.set_yticklabels(ampsx_times, fontsize=8)
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

    # Colormap for .freqsx files
    fig, ax = plt.subplots(figsize=(max(12, len(bpm_columns)//3), max(8, len(freqsx_files)//4)))
    im = ax.imshow(np.array(freqsx_presence_matrix), aspect='auto', cmap='plasma', vmin=0, vmax=1)
    ax.set_xlabel('BPM Name', fontsize=14)
    ax.set_ylabel('File (Time)', fontsize=14)
    ax.set_title(f'BPM presence in .freqsx files ({date})', fontsize=16)
    ax.set_xticks(np.arange(len(bpm_columns)))
    ax.set_xticklabels(bpm_columns, rotation=90, fontsize=7)
    ax.set_yticks(np.arange(len(freqsx_times)))
    ax.set_yticklabels(freqsx_times, fontsize=8)
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

# --- Save lost BPMs (counts and names) as JSON ---
lost_bpm_info = []
for i, time in enumerate(times):
    if lost_data_sdds[i] is None:
        continue
    datafile = os.path.join(data_dir, f"{date}_{time}.data")
    sddsfile = os.path.join(sdds_dir, f"{date}_{time}.sdds")
    ampsxfile = os.path.join(harmonic_dir, f"{date}_{time}.sdds.ampsx")
    freqsxfile = os.path.join(harmonic_dir, f"{date}_{time}.sdds.freqsx")

    with open(datafile, "r") as f:
        data = f.read()
    bpm_names_data = set(re.findall(r'"([^"]+)"->', data))

    bpm_names_sdds = set()
    with open(sddsfile, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            match = re.match(r'\s*\d+\s+(\S+)', line)
            if match:
                bpm_names_sdds.add(match.group(1))

    bpm_names_ampsx = set()
    with open(ampsxfile, "r") as f:
        for line in f:
            if line.startswith("*"):
                bpm_names_ampsx = set(line.split()[1:])
                break

    bpm_names_freqsx = set()
    with open(freqsxfile, "r") as f:
        for line in f:
            if line.startswith("*"):
                bpm_names_freqsx = set(line.split()[1:])
                break

    lost_in_sdds = sorted(bpm_names_data - bpm_names_sdds)
    lost_in_ampsx = sorted(bpm_names_data - bpm_names_ampsx)
    lost_in_freqsx = sorted(bpm_names_data - bpm_names_freqsx)

    lost_bpm_info.append({
        "time": time,
        "lost_in_sdds_count": len(lost_in_sdds),
        "lost_in_sdds_names": lost_in_sdds,
        "lost_in_ampsx_count": len(lost_in_ampsx),
        "lost_in_ampsx_names": lost_in_ampsx,
        "lost_in_freqsx_count": len(lost_in_freqsx),
        "lost_in_freqsx_names": lost_in_freqsx
    })

with open(os.path.join(output_dir, f"bpms_lost_details_{typed}.json"), "w") as jsonfile:
    json.dump(lost_bpm_info, jsonfile, indent=2)