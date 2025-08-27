'''
Class method to read and process experimental or tracking data files.
Plots position data for specified BPMs, spectra and Resonance Driving Terms (RDTs).
'''

import os
import glob
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import logging
import tfs

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

mpl.rcParams.update({
    'font.size': 20,
    "text.usetex": False,
    "font.family": "Arial"
})

class DataPlotter:
      def __init__(self, base_path):
            """
            Initialize the DataPlotter with the base path.
            """
            self.base_path = base_path
            self.sdds_path = os.path.join(base_path, "synched_sdds")
            self.harmonic_path = os.path.join(base_path, "synched_harmonic")
            self.output_path = os.path.join(base_path, "plots")
            os.makedirs(self.output_path, exist_ok=True)

      def list_files(self, folder, extension):
            """
            List all files in a folder with the given extension.
            """
            return sorted(glob.glob(os.path.join(folder, f"*.{extension}")))

      def extract_date_from_filename(self, filename):
            """
            Extract the date and time in the format 'YYYY_MM_DD_hh_mm_ss' from the filename.
            Example: 'HER_2024_06_17_12_30_45.sdds' -> '2024_06_17_12_30_45'
            """
            base_name = os.path.basename(filename)
            parts = base_name.split('_')
            if len(parts) >= 6 and parts[-1].split('.')[0].isdigit():  # Check for YYYY_MM_DD_hh_mm_ss format
                  #print(f"{parts[1]}_{parts[2]}_{parts[3]}_{parts[4]}_{parts[5]}_{parts[6].split('.')[0]}")
                  return f"{parts[1]}_{parts[2]}_{parts[3]}_{parts[4]}_{parts[5]}_{parts[6].split('.')[0]}"
            return "Unknown_Date_Time"

      def plot_positions(self, bpm_list=None, axis="x", date=None):
            """
            Plot particle positions from .sdds files for a specific date or all files in the folder.
            """
            # Define the desired BPM order
            bpm_order = ["MQC1LE", "MQC2LE", "MQLC3LE", "MQLC7LE", "MQLB1LE", "MQLB4LE", "MQLA2LE", "MQLA5LE",
                         "MQD3E1", "MQEAE4", "MQD3E4", "MQEAE6", "MQTATNE1", "MQTATNE2", "MQEAE8", "MQD3E8",
                         "MQEAE10", "MQEAE11", "MQR2NE1", "MQFRNE3", "MQDRNE5", "MQEAE13", "MQD3E12", "MQEAE16",
                         "MQD3E14", "MQEAE18", "MQTANFE1", "MQD3E16", "MQEAE20", "MQD3E18", "MQEAE22", "MQEAE23",
                         "MQI6E", "MQI5E", "MQI4E", "MQX2RE", "MQM2E", "MQM7E", "MQEAE25", "MQD3E21", "MQEAE27",
                         "MQD3E23", "MQEAE29", "MQEAE30", "MQTAFOE1", "MQTAFOE2", "MQEAE32", "MQD3E29", "MQEAE35",
                         "MQR2ORE", "MQDROE5", "MQEAE37", "MQD3E31", "MQEAE39", "MQD3E33", "MQEAE41", "MQTAOTE1",
                         "MQTAOTE2", "MQEAE44", "MQEAE45", "MQD3E40", "MQLA2RE", "MQLB8RE", "MQLB1RE", "MQLC7RE",
                         "MQLC3RE", "MQC2RE", "MQC1RE"]

            # If a date is provided, filter files for that date; otherwise, use all files
            if date:
                  files = [os.path.join(self.sdds_path, f"{date}.sdds")]
            else:
                  files = self.list_files(self.sdds_path, "sdds")

            if not files:
                  logging.warning(f"No .sdds files found for axis {axis.upper()} and date {date or 'ALL'}.")
                  return

            pdf_filename = os.path.join(self.output_path, f"Positions_{axis.upper()}_{date or 'ALL'}.pdf")
            with PdfPages(pdf_filename) as pdf:
                  for file in files:
                        date_time = self.extract_date_from_filename(file)
                        title = f"HER_{date_time}"

                        try:
                              with open(file) as fo:
                                    lines = fo.readlines()[11:]  # Skip the header line
                        except Exception as e:
                              logging.error(f"Error reading file {file}: {e}")
                              continue

                        bpm_positions = []
                        for line in lines:
                              parts = line.split()
                              if len(parts) < 4:
                                    continue
                              line_axis = 'x' if parts[0] == '0' else 'y'
                              if line_axis != axis:
                                    continue
                              bpm = parts[1]
                              if bpm_list and bpm not in bpm_list:
                                    continue
                              orbit = [float(val) for val in parts[3:] if val != "0"]
                              bpm_positions.append((bpm, orbit))

                        # Sort BPMs based on the desired order
                        bpm_positions.sort(key=lambda x: bpm_order.index(x[0]) if x[0] in bpm_order else float('inf'))

                        if not bpm_positions:
                              continue

                        fig, axes = plt.subplots(len(bpm_positions), 1, figsize=(10, 4.5 * len(bpm_positions)), sharex=False)
                        if len(bpm_positions) == 1:
                              axes = [axes]

                        for idx, (bpm, orbit) in enumerate(bpm_positions):
                              ax = axes[idx]
                              turns = np.arange(len(orbit))
                              ax.scatter(turns[1:], orbit[1:], s=5, marker="o", label=f"{axis.upper()} plane")
                              ax.set_xlabel("Turn Number")
                              ax.set_ylabel("Bunch Centroid [mm]")
                              ax.legend(markerscale=3)
                              ax.tick_params("both")
                              ax.set_title(f"BPM {bpm} - {title}")
                              ax.set_xlim(0, len(turns) - 1)

                        plt.tight_layout(rect=[0, 0.05, 1, 1])
                        plt.subplots_adjust(hspace=0.5)
                        pdf.savefig(fig, dpi=100, bbox_inches="tight")
                        plt.close(fig)

            logging.info(f"Particle position plots saved in {pdf_filename}.")

      def plot_spectra(self, bpm_list=None, axis="x", date=None):
            """
            Plot spectra from .amps and .freq files for a specific date or all files in the folder.
            Ensures that the date of the amps file matches the date of the corresponding freqs file.
            """
            # Determine file extensions based on the axis
            amps_extension = "sdds.ampsx" if axis == "x" else "sdds.ampsy"
            freqs_extension = "sdds.freqsx" if axis == "x" else "sdds.freqsy"

            # Define the desired BPM order
            bpm_order = ["MQC1LE", "MQC2LE", "MQLC3LE", "MQLC7LE", "MQLB1LE", "MQLB4LE", "MQLA2LE", "MQLA5LE",
                         "MQD3E1", "MQEAE4", "MQD3E4", "MQEAE6", "MQTATNE1", "MQTATNE2", "MQEAE8", "MQD3E8",
                         "MQEAE10", "MQEAE11", "MQR2NE1", "MQFRNE3", "MQDRNE5", "MQEAE13", "MQD3E12", "MQEAE16",
                         "MQD3E14", "MQEAE18", "MQTANFE1", "MQD3E16", "MQEAE20", "MQD3E18", "MQEAE22", "MQEAE23",
                         "MQI6E", "MQI5E", "MQI4E", "MQX2RE", "MQM2E", "MQM7E", "MQEAE25", "MQD3E21", "MQEAE27",
                         "MQD3E23", "MQEAE29", "MQEAE30", "MQTAFOE1", "MQTAFOE2", "MQEAE32", "MQD3E29", "MQEAE35",
                         "MQR2ORE", "MQDROE5", "MQEAE37", "MQD3E31", "MQEAE39", "MQD3E33", "MQEAE41", "MQTAOTE1",
                         "MQTAOTE2", "MQEAE44", "MQEAE45", "MQD3E40", "MQLA2RE", "MQLB8RE", "MQLB1RE", "MQLC7RE",
                         "MQLC3RE", "MQC2RE", "MQC1RE"]

            # If a date is provided, filter files for that date; otherwise, use all files
            if date:
                  amps_files = [os.path.join(self.harmonic_path, f"{date}.{amps_extension}")]
                  freqs_files = [os.path.join(self.harmonic_path, f"{date}.{freqs_extension}")]
            else:
                  amps_files = self.list_files(self.harmonic_path, amps_extension)
                  freqs_files = self.list_files(self.harmonic_path, freqs_extension)

            if not amps_files or not freqs_files:
                  logging.warning(f"No harmonic files found for axis {axis.upper()} and date {date or 'ALL'}.")
                  return

            pdf_filename = os.path.join(self.output_path, f"Spectra_{axis.upper()}_{date or 'ALL'}.pdf")
            with PdfPages(pdf_filename) as pdf:
                  for amps_file, freqs_file in zip(amps_files, freqs_files):
                        # Extract dates from the filenames
                        amps_date_time = self.extract_date_from_filename(amps_file)
                        freqs_date_time = self.extract_date_from_filename(freqs_file)

                        # Check if the dates match
                        if amps_date_time != freqs_date_time:
                              logging.warning(f"Date mismatch: {amps_file} ({amps_date_time}) and {freqs_file} ({freqs_date_time}). Skipping.")
                              continue

                        title = f"HER_{amps_date_time}"

                        try:
                              amps_data = tfs.read_tfs(amps_file)
                              freqs_data = tfs.read_tfs(freqs_file)
                        except Exception as e:
                              logging.error(f"Error reading files {amps_file} or {freqs_file}: {e}")
                              continue

                        # Ensure column names are stripped of whitespace
                        amps_data.columns = amps_data.columns.str.strip()
                        freqs_data.columns = freqs_data.columns.str.strip()

                        bpm_columns = bpm_list if bpm_list else amps_data.columns

                        # Sort BPMs based on the desired order
                        bpm_columns = sorted(bpm_columns, key=lambda x: bpm_order.index(x) if x in bpm_order else float('inf'))

                        for bpm in bpm_columns:
                              if bpm not in amps_data.columns or bpm not in freqs_data.columns:
                                    continue

                              amplitude_data = amps_data[bpm]
                              frequency_data = freqs_data[bpm]

                              # Find the maximum amplitude and its corresponding frequency
                              max_idx = np.argmax(amplitude_data)
                              max_frequency = frequency_data.iloc[max_idx]
                              max_amplitude = amplitude_data.iloc[max_idx]

                              fig, ax = plt.subplots(figsize=(10, 6))
                              plt.yscale('log')
                              ax.plot(frequency_data, amplitude_data, lw=1, label=f"{axis.upper()} plane")
                              ax.fill_between(frequency_data, amplitude_data, color='blue', alpha=0.5)

                              # Add a vertical line at the maximum amplitude
                              ax.axvline(x=max_frequency, color='red', linestyle='--', label=f"Max @ {max_frequency:.4f}")
                              #ax.axvline(x=0.3840, color='red', linestyle='--', label=f"Max @ 0.3840")

                              ax.set_xlabel('Fractional Tune')
                              ax.set_ylabel('Amplitude [mm]')
                              ax.set_title(f"BPM {bpm} - {title}")
                              ax.grid(which='major', axis='x', linestyle=':', linewidth=0.7)
                              ax.grid(which='both', axis='y', linestyle=':', linewidth=0.7)
                              ax.minorticks_on()
                              ax.legend()
                              pdf.savefig(fig, dpi=150, bbox_inches='tight')
                              plt.close(fig)

            logging.info(f"Spectra plots saved in {pdf_filename}.")

      def plot_RDT(self, multipole, rdt, axis="x"):
            """
            Plot the S (position) vs. AMP (amplitude) with error bars for a given multipole, RDT, and axis.

            Args:
                multipole (str): The name of the multipole (e.g., "normal_quadrupole").
                rdt (str): The RDT (e.g., "f1012").
                axis (str): The plane ("x" or "y").
            """
            # Construct the file path
            file_path = os.path.join(
                  self.base_path,
                  "synched_optics",
                  "average",
                  "rdt",
                  multipole,
                  f"{rdt}_{axis}.tfs"
            )

            # Check if the file exists
            if not os.path.exists(file_path):
                  logging.error(f"File not found: {file_path}")
                  return

            try:
                  # Read the .tfs file
                  with open(file_path, 'r') as file:
                        lines = file.readlines()

                  # Find the start of the data table
                  for i, line in enumerate(lines):
                        if line.startswith('*'):  # Column names
                              column_names = line.split()
                        if line.startswith('$'):  # Data types
                              data_start_index = i + 1
                              break

                  # Extract the data
                  data = []
                  for line in lines[data_start_index:]:
                        if line.strip():  # Skip empty lines
                              data.append(line.split())

                  # Convert data to a dictionary for easier access
                  data_dict = {col: [] for col in column_names[1:]}  # Skip the '*' symbol
                  for row in data:
                        for col, value in zip(column_names[1:], row):
                              data_dict[col].append(value)

                  # Convert S, AMP, and ERRAMP columns to floats
                  s_values = list(map(float, data_dict["S"]))
                  amp_values = list(map(float, data_dict["AMP"]))
                  erramp_values = list(map(float, data_dict["ERRAMP"]))

                  # Extract numbers from the RDT string
                  rdt_numbers = [int(digit) for digit in rdt[1:]]  # Skip the 'f' prefix
                  rdt_sum = sum(rdt_numbers)  # Sum the numbers
                  power = 1 - (rdt_sum / 2)  # Calculate the power for the unit

                  # Generate the Y-axis label dynamically in LaTeX format
                  y_label = f"$|f_{{{''.join(map(str, rdt_numbers))},{axis}}}|$ [m$^{{{power:.0f}}}$]"

                  # Plot S vs. AMP with error bars
                  plt.figure(figsize=(10, 6))
                  plt.errorbar(s_values, amp_values, yerr=erramp_values, fmt='o', linestyle='-', linewidth=1, 
                                    label=f"{multipole.split('_')[0].capitalize()} {multipole.split('_')[1].capitalize()}", markersize=5, capsize=3)
                  plt.xlabel("Position [m]")
                  plt.ylabel(y_label)
                  # plt.title(f"{multipole.capitalize()}")
                  plt.legend()
                  plt.grid(True)
                  plt.tight_layout()

                  # Save the plot
                  output_file = os.path.join(self.output_path, f"{multipole}_{rdt}_{axis.upper()}.pdf")
                  plt.savefig(output_file)
                  plt.close()

                  logging.info(f"Plot saved as: {output_file}")

            except Exception as e:
                  logging.error(f"Error processing file {file_path}: {e}")


# Example usage
# base_path = "/home/andym/Documents/SOMA/SOMA/output/output_track_scaled_HER_2024_06_17/"
base_path = "/home/andym/Documents/SOMA/SOMA/output/output_short_HER_2024_06_17/"
plotter = DataPlotter(base_path)

# Plot particle positions
# plotter.plot_positions(bpm_list=["MQC1LE"], axis="x", date="HER_2024_06_17_17_53_37")
# plotter.plot_positions(bpm_list=["MQC1LE"], axis="y", date="HER_2024_06_17_17_53_37")

# Plot spectra
# plotter.plot_spectra(bpm_list=["MQC1LE"], axis="x", date="HER_2024_06_17_17_53_37")
# plotter.plot_spectra(bpm_list=["MQC1LE"], axis="y", date="HER_2024_06_17_17_53_37")
plotter.plot_spectra(bpm_list=None, axis="x", date="HER_2024_06_17_17_53_37")
plotter.plot_spectra(bpm_list=None, axis="y", date="HER_2024_06_17_17_53_37")

# Plot RDT
# plotter.plot_RDT(multipole="skew_octupole", rdt="f1210", axis="x")
# plotter.plot_RDT(multipole="skew_octupole", rdt="f1012", axis="y")
# plotter.plot_RDT(multipole="skew_sextupole", rdt="f1101", axis="x")
# plotter.plot_RDT(multipole="skew_sextupole", rdt="f0012", axis="y")