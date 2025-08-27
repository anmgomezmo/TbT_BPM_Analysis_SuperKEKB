'''
Reading and procesing tracking files after SOMA analysis
'''

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib as mpl
import tfs
import logging
import colorlog

# Configure colored logging
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }
))

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

mpl.rcParams.update({
    'font.size': 14,
    "text.usetex": False,
    "font.family": "Arial"
})


# --- Section 0: Helper functions ---
def extract_selected_value(filename):
    """
    Extracts the selected_value from a filename.
    Example: "zx_1.0.sdds" -> 1.0
    """
    try:
        parts = filename.split('_')
        if len(parts) > 1:
            value = float(parts[1].split('.')[0] + '.' + parts[1].split('.')[1])
            return value
    except ValueError:
        logging.warning(f"Could not extract selected_value from filename: {filename}")
    return None


def read_files_from_directory(directory, extensions):
    """
    Reads files from a directory and organizes them by selected_value.
    """
    file_map = {}
    selected_values = set()

    for ext in extensions:
        files = glob.glob(os.path.join(directory, f"*.{ext}"))
        for file in files:
            base_name = os.path.basename(file)
            value = extract_selected_value(base_name)
            if value is not None:
                selected_values.add(value)
                if value not in file_map:
                    file_map[value] = {ext: [] for ext in extensions}
                file_map[value][ext].append(file)

    # Sort the file_map and selected_values
    file_map = {k: file_map[k] for k in sorted(file_map)}
    selected_values = sorted(selected_values)
    logging.info(f"Detected selected_values: {selected_values}")
    return file_map, selected_values


# --- Section 1: Plotting particle positions in BPMs from SDDS files ---
class PositionPlotter:
    def __init__(self, config):
        """
        Initialize the PositionPlotter with paths.
        Automatically sets up output_dir.
        """
        self.input_path = config["input_path"]
        self.output_dir = os.path.join(self.input_path, "plotPositions/")
        os.makedirs(self.output_dir, exist_ok=True)
        self.file_map = {}
        self.selected_values = []

    def read_files(self):
        """
        Reads .sdds files and organizes them by selected_value.
        """
        self.file_map, self.selected_values = read_files_from_directory(os.path.join(self.input_path, "unsynched_sdds_partial/"), ["sdds"])

    def plot_positions(self, bpm_list=None, axis="x", selected_values=None):
        """
        Plots particle positions for the specified BPMs in a single PDF file for the given axis.
        If bpm_list is None, plots for all BPMs.
        If selected_values is None, plots for all detected selected_values.
        """
        if axis not in ["x", "y"]:
            raise ValueError("Invalid axis. Choose 'x' or 'y'.")

        pdf_filename = os.path.join(self.output_dir, f"Positions_{axis.upper()}.pdf")
        values_to_plot = selected_values if selected_values else self.selected_values

        with PdfPages(pdf_filename) as pdf:
            for value in values_to_plot:
                if value not in self.file_map:
                    logging.warning(f"Selected value {value} not found in loaded files.")
                    continue

                files = self.file_map[value]["sdds"]
                if not files:
                    logging.warning(f"No .sdds files found for selected value {value}.")
                    continue

                for file in files:
                    try:
                        with open(file) as fo:
                            lines = fo.readlines()[1:]  # Skip the header line
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

                    if not bpm_positions:
                        continue

                    fig, axes = plt.subplots(len(bpm_positions), 1, figsize=(10, 4.5 * len(bpm_positions)), sharex=False)
                    if len(bpm_positions) == 1:
                        axes = [axes]

                    for idx, (bpm, orbit) in enumerate(bpm_positions):
                        ax = axes[idx]
                        turns = np.arange(len(orbit))
                        ax.scatter(turns, orbit, s=5, marker="o", label=f"{axis.upper()} plane")
                        ax.set_xlabel("Turn Number")
                        ax.set_ylabel("Bunch Centroid [mm]")
                        ax.legend(markerscale=3)
                        ax.tick_params("both")
                        ax.set_title(f"BPM {bpm} - Action {value}")
                        ax.set_xlim(0, len(turns) - 1)

                    plt.tight_layout(rect=[0, 0.05, 1, 1])
                    plt.subplots_adjust(hspace=0.5)
                    pdf.savefig(fig, dpi=100, bbox_inches="tight")
                    plt.close(fig)

        logging.info(f"Combined {axis.upper()}-axis position plots saved in {pdf_filename}.")

    def plot_positions_for_value(self, selected_value, bpm_list, title_prefix="HER"):
        """
        Plots positions for a list of BPMs for a single selected_value.
        Creates two PDF files (X and Y planes) with vertical arrangement of plots.
        Each subplot is labeled with letters (a, b, c...) and includes BPM name.

        Args:
            selected_value (float): The specific selected value to plot
            bpm_list (list): List of BPM names to plot
            title_prefix (str): Prefix for subplot labels (default: "HER")
        """
        if selected_value not in self.file_map:
            logging.warning(f"Selected value {selected_value} not found in loaded files.")
            return

        for axis in ["x", "y"]:
            pdf_filename = os.path.join(self.output_dir, f"Positions_{axis.upper()}_value_{selected_value}.pdf")

            with PdfPages(pdf_filename) as pdf:
                # Collect all position data for the BPMs in the list
                bpm_positions = []

                files = self.file_map[selected_value]["sdds"]
                if not files:
                    logging.warning(f"No .sdds files found for selected value {selected_value}.")
                    continue

                for file in files:
                    try:
                        with open(file) as fo:
                            lines = fo.readlines()[1:]  # Skip the header line
                    except Exception as e:
                        logging.error(f"Error reading file {file}: {e}")
                        continue

                    # Extract positions for all requested BPMs
                    for line in lines:
                        parts = line.split()
                        if len(parts) < 4:
                            continue

                        line_axis = 'x' if parts[0] == '0' else 'y'
                        if line_axis != axis:
                            continue

                        bpm = parts[1]
                        # print(f"Axis: {line_axis}, BPM: '{bpm}', BPMs to plot: {bpm_list}")
                        if bpm not in bpm_list:
                            continue

                        # print(bpm)        
                        orbit = [float(val) for val in parts[3:] if val != "0"]
                        bpm_positions.append((bpm, orbit))

                if not bpm_positions:
                    logging.warning(f"No position data found for the requested BPMs in {axis}-axis.")
                    continue

                # Create figure with subplots
                fig, axes = plt.subplots(len(bpm_positions), 1, figsize=(10, 4 * len(bpm_positions)), sharex=False)
                if len(bpm_positions) == 1:
                    axes = [axes]

                # Plot each BPM with appropriate label
                for idx, (bpm, orbit) in enumerate(bpm_positions):
                    ax = axes[idx]
                    turns = np.arange(len(orbit))

                    ax.scatter(turns, orbit, s=5, marker="o", label=f"{axis.upper()} plane")

                    # Add letter label
                    subplot_letter = chr(97 + idx)  # 97 is ASCII for 'a'
                    #ax.set_title(f"BPM {bpm} - Action {selected_value}")

                    ax.set_xlabel("Turn Number")
                    ax.set_ylabel("Bunch Centroid [mm]")

                    # Add the letter label below the x-axis
                    ax.text(0.37, -0.40, f"{subplot_letter}) {title_prefix} BPM {bpm}",
                            transform=ax.transAxes, fontsize=14)

                    ax.legend(markerscale=3)
                    ax.tick_params("both")
                    ax.set_xlim(0, len(turns) - 1)

                plt.tight_layout(rect=[0, 0.03, 1, 0.97])
                plt.subplots_adjust(hspace=0.53)
                pdf.savefig(fig, dpi=150, bbox_inches="tight")
                plt.close(fig)

            logging.info(f"Combined {axis.upper()}-axis position plots for value {selected_value} saved in {pdf_filename}.")



# --- Section 2: Plotting FFT spectrum from .amps and .freq files ---
class SpectrumPlotter:
    def __init__(self, config):
        """
        Initialize the SpectrumPlotter with paths.
        Automatically sets up output_dir and common_path.
        """
        self.input_path = config["input_path"]
        self.output_dir = os.path.join(self.input_path, "plotFrequ/")
        self.common_path = os.path.join(self.input_path, "synched_harmonic_partial/")
        os.makedirs(self.output_dir, exist_ok=True)
        self.file_map = {}
        self.selected_values = []

    def read_files(self):
        """
        Reads .amps and .freq files for X and Y axes from the folder.
        """
        self.file_map, self.selected_values = read_files_from_directory(self.common_path, ["ampsx", "ampsy", "freqsx", "freqsy"])

    def plot_spectra(self, selected_value, bpm_list=None, axis="x", freq_range=(0.45, 0.47)):
        """
        Plots all spectra for the specified BPMs in a single PDF file for the given axis and selected value.
        If bpm_list is None, plots for all BPMs.
        Finds the maximum amplitude within the specified frequency range.

        Args:
            selected_value (float): The selected value to filter files.
            bpm_list (list): List of BPMs to plot. If None, plots all BPMs.
            axis (str): The axis ("x" or "y").
            freq_range (tuple): The frequency range to find the maximum amplitude (default: (0.45, 0.47)).
        """
        if selected_value not in self.file_map:
            raise ValueError(f"Selected value {selected_value} not found in loaded files.")

        if axis == "x":
            amps_files = self.file_map[selected_value]["ampsx"]
            freqs_files = self.file_map[selected_value]["freqsx"]
            pdf_filename = os.path.join(self.output_dir, f"Spectras_action_{selected_value}_X.pdf")
        elif axis == "y":
            amps_files = self.file_map[selected_value]["ampsy"]
            freqs_files = self.file_map[selected_value]["freqsy"]
            pdf_filename = os.path.join(self.output_dir, f"Spectras_action_{selected_value}_Y.pdf")
        else:
            raise ValueError("Invalid axis. Choose 'x' or 'y'.")

        with PdfPages(pdf_filename) as pdf:
            for amps_file, freqs_file in zip(amps_files, freqs_files):
                amps_data = tfs.read_tfs(amps_file)
                freqs_data = tfs.read_tfs(freqs_file)

                # Ensure column names are stripped of whitespace
                amps_data.columns = amps_data.columns.str.strip()
                freqs_data.columns = freqs_data.columns.str.strip()

                # Filter BPMs if a list is provided
                bpm_columns = bpm_list if bpm_list else amps_data.columns

                for BPM in bpm_columns:
                    if BPM not in amps_data.columns or BPM not in freqs_data.columns:
                        continue

                    amplitude_data = amps_data[BPM]
                    frequency_data = freqs_data[BPM]

                    # Filter data within the specified frequency range
                    mask = (frequency_data >= freq_range[0]) & (frequency_data <= freq_range[1])
                    filtered_amplitude = amplitude_data[mask]
                    filtered_frequency = frequency_data[mask]

                    # Find the maximum amplitude and its corresponding frequency within the range
                    if len(filtered_amplitude) > 0:
                        max_idx = np.argmax(filtered_amplitude)
                        max_frequency = filtered_frequency.iloc[max_idx]
                        max_amplitude = filtered_amplitude.iloc[max_idx]
                    else:
                        max_frequency = None
                        max_amplitude = None

                    fig, ax = plt.subplots(figsize=(10, 6))
                    plt.yscale('log')  # Set y-axis to logarithmic scale
                    ax.plot(frequency_data, amplitude_data, lw=1, label=f"{axis.upper()} plane")
                    ax.fill_between(frequency_data, amplitude_data, color='blue', alpha=0.5)

                    # Add a vertical line at the maximum amplitude within the range
                    if max_frequency is not None:
                        ax.axvline(x=max_frequency, color='red', linestyle='--', label=f"Max @ {max_frequency:.4f}")
                        #ax.text(max_frequency, max_amplitude, f"{max_amplitude:.2e}", color='red', fontsize=10)

                    ax.set_xlabel('Fractional Tune')
                    ax.set_ylabel('Amplitude [mm]')
                    ax.set_title(f"BPM {BPM} - Action {selected_value}")
                    ax.grid(which='major', axis='x', linestyle=':', linewidth=0.7)
                    ax.grid(which='both', axis='y', linestyle=':', linewidth=0.7)
                    ax.minorticks_on()
                    ax.legend()
                    pdf.savefig(fig, dpi=150, bbox_inches='tight')
                    plt.close(fig)

        logging.info(f"Combined {axis.upper()}-axis plots for {selected_value} saved in {pdf_filename}.")

    def plot_all_spectra(self, bpm_list=None, axis="x"):
        """
        Plots spectra for all selected values in the list.
        Generates a single PDF file for the specified axis.
        """
        if axis == "x":
            pdf_filename = os.path.join(self.output_dir, f"Spectras_action_All_X.pdf")
        elif axis == "y":
            pdf_filename = os.path.join(self.output_dir, f"Spectras_action_All_Y.pdf")
        else:
            raise ValueError("Invalid axis. Choose 'x' or 'y'.")

        with PdfPages(pdf_filename) as pdf:
            for selected_value, files in self.file_map.items():
                amps_files = files["ampsx"] if axis == "x" else files["ampsy"]
                freqs_files = files["freqsx"] if axis == "x" else files["freqsy"]
                #print(amps_files, freqs_files)  # Debugging output to check loaded files

                for amps_file, freqs_file in zip(amps_files, freqs_files):
                    amps_data = tfs.read_tfs(amps_file)
                    freqs_data = tfs.read_tfs(freqs_file)

                    # Ensure column names are stripped of whitespace
                    amps_data.columns = amps_data.columns.str.strip()
                    freqs_data.columns = freqs_data.columns.str.strip()
                    #print(amps_data.columns, freqs_data.columns)  # Debugging output to check column names

                    # Filter BPMs if a list is provided
                    bpm_columns = bpm_list if bpm_list else amps_data.columns

                    for BPM in bpm_columns:
                        if BPM not in amps_data.columns or BPM not in freqs_data.columns:
                            continue

                        amplitude_data = amps_data[BPM] #* 1e3  # Example scaling
                        frequency_data = freqs_data[BPM]

                        # Find the maximum amplitude and its corresponding frequency
                        max_idx = np.argmax(amplitude_data)
                        max_frequency = frequency_data.iloc[max_idx]
                        max_amplitude = amplitude_data.iloc[max_idx]

                        # Plot the spectrum
                        fig, ax = plt.subplots(figsize=(10, 6))
                        plt.yscale('log')  # Set y-axis to logarithmic scale
                        ax.plot(frequency_data, amplitude_data, lw=1, label=f"{axis.upper()} plane")
                        ax.fill_between(frequency_data, amplitude_data, color='blue', alpha=0.5)

                        # Add a vertical line at the maximum amplitude
                        ax.axvline(x=max_frequency, color='red', linestyle='--', label=f"Max @ {max_frequency:.4f}")

                        # Set labels and title
                        ax.set_xlabel('Fractional Tune')
                        ax.set_ylabel('Amplitude [mm]')
                        ax.set_title(f"BPM {BPM} - Action {selected_value}")
                        ax.grid(which='major', axis='x', linestyle=':', linewidth=0.7)
                        ax.grid(which='both', axis='y', linestyle=':', linewidth=0.7)
                        ax.minorticks_on()
                        ax.legend()

                        # Save the plot to the PDF
                        pdf.savefig(fig, dpi=150, bbox_inches='tight')
                        plt.close(fig)

        logging.info(f"Combined {axis.upper()}-axis plots for all selected values saved in {pdf_filename}.")

    def plot_spectra_grid(self, selected_value, bpm_list, title_prefix="HER", freq_range=(0.45, 0.47)):
        """
        Plots spectra for a list of BPMs in a grid layout (n rows, 2 columns) for a single selected value.
        Creates two PDF files (X and Y planes).
        Each subplot is labeled with letters (a, b, c...) and includes BPM name.

        Args:
            selected_value (float): The specific selected value to plot
            bpm_list (list): List of BPM names to plot
            title_prefix (str): Prefix for subplot labels (default: "HER")
            freq_range (tuple): The frequency range to find and mark peak (default: (0.45, 0.47))
        """
        if selected_value not in self.file_map:
            logging.warning(f"Selected value {selected_value} not found in loaded files.")
            return

        for axis in ["x", "y"]:
            pdf_filename = os.path.join(self.output_dir, f"Spectras_Grid_{axis.upper()}_value_{selected_value}.pdf")

            # Determine data files
            if axis == "x":
                amps_files = self.file_map[selected_value]["ampsx"]
                freqs_files = self.file_map[selected_value]["freqsx"]
            else:
                amps_files = self.file_map[selected_value]["ampsy"]
                freqs_files = self.file_map[selected_value]["freqsy"]

            if not amps_files or not freqs_files:
                logging.warning(f"No amplitude or frequency files found for {axis}-axis with selected value {selected_value}")
                continue

            # Read data files
            bpm_data = {}
            for amps_file, freqs_file in zip(amps_files, freqs_files):
                amps_data = tfs.read_tfs(amps_file)
                freqs_data = tfs.read_tfs(freqs_file)

                # Ensure column names are stripped of whitespace
                amps_data.columns = amps_data.columns.str.strip()
                freqs_data.columns = freqs_data.columns.str.strip()

                # Collect data for the requested BPMs
                for bpm in bpm_list:
                    if bpm in amps_data.columns and bpm in freqs_data.columns:
                        bpm_data[bpm] = {
                            'amplitude': amps_data[bpm],
                            'frequency': freqs_data[bpm]
                        }

            if not bpm_data:
                logging.warning(f"No data found for the requested BPMs in {axis}-axis")
                continue

            # Add the missing with statement here
            with PdfPages(pdf_filename) as pdf:
                # Calculate grid dimensions
                num_bpms = len(bpm_data)
                num_rows = (num_bpms + 1) // 2  # Ceiling division to get number of rows

                # Create figure with subplots
                fig, axes = plt.subplots(num_rows, 2, figsize=(16, 6 * num_rows))
                if num_rows == 1:
                    axes = np.array([axes])  # Ensure axes is always a 2D array

                # Plot each BPM with appropriate label
                for idx, bpm in enumerate(bpm_data.keys()):
                    row = idx // 2
                    col = idx % 2

                    ax = axes[row, col]

                    amplitude_data = bpm_data[bpm]['amplitude']
                    frequency_data = bpm_data[bpm]['frequency']

                    # Filter data within the specified frequency range for peak finding
                    mask = (frequency_data >= freq_range[0]) & (frequency_data <= freq_range[1])
                    filtered_amplitude = amplitude_data[mask]
                    filtered_frequency = frequency_data[mask]

                    # Find the maximum amplitude and its corresponding frequency within range
                    if len(filtered_amplitude) > 0:
                        max_idx = np.argmax(filtered_amplitude)
                        max_frequency = filtered_frequency.iloc[max_idx]
                        max_amplitude = filtered_amplitude.iloc[max_idx]
                    else:
                        max_frequency = None
                        max_amplitude = None

                    # Plot spectrum
                    ax.set_yscale('log')
                    ax.plot(frequency_data, amplitude_data, lw=1, label=f"{axis.upper()} plane")
                    ax.fill_between(frequency_data, amplitude_data, color='blue', alpha=0.5)

                    # Add vertical line at peak
                    # if max_frequency is not None:
                    #     ax.axvline(x=max_frequency, color='red', linestyle='--',
                    #                label=f"Max @ {max_frequency:.4f}")

                    # Add letter label
                    subplot_letter = chr(97 + idx)  # 97 is ASCII for 'a'

                    # Set labels
                    ax.set_xlabel('Fractional Tune')
                    ax.set_ylabel('Amplitude [mm]')

                    # Add the letter label below the x-axis
                    ax.text(0.32, -0.25, f"{subplot_letter}) {title_prefix} BPM {bpm}",
                            transform=ax.transAxes, fontsize=16)

                    ax.grid(which='major', axis='x', linestyle=':', linewidth=0.7)
                    ax.grid(which='both', axis='y', linestyle=':', linewidth=0.7)
                    ax.minorticks_on()
                    ax.legend()

                # Hide any unused subplots
                for idx in range(len(bpm_data), num_rows * 2):
                    row = idx // 2
                    col = idx % 2
                    axes[row, col].axis('off')

                plt.tight_layout(rect=[0, 0.03, 1, 0.97])
                plt.subplots_adjust(hspace=0.35, wspace=0.3)
                pdf.savefig(fig, dpi=150, bbox_inches='tight')
                plt.close(fig)

            logging.info(f"Grid of {axis.upper()}-axis spectrum plots for value {selected_value} saved in {pdf_filename}.")


# Example usage
config = {
    "input_path": "/home/andym/Documents/SOMA/SOMA/output/output_track_scaled_HER_2024_06_17/"
}

position_plotter = PositionPlotter(config)
position_plotter.read_files()
# position_plotter.plot_positions(bpm_list=["MQC1LE","MQEAE16","MQD3E14","MQI5E"], axis="x", selected_values=[4.0])
# position_plotter.plot_positions(bpm_list=["MQC1LE","MQEAE16","MQD3E14","MQI5E"], axis="y", selected_values=[4.0])
# position_plotter.plot_positions_for_value(4.0, ["MQC2LE","MQEAE16","MQD3E14","MQI5E"])
# position_plotter.plot_positions_for_value(31, ["MQC1LE"])

spectrum_plotter = SpectrumPlotter(config)
spectrum_plotter.read_files()
# spectrum_plotter.plot_spectra(selected_value=4.0, bpm_list=["MQC1LE"], axis="x", freq_range=(0.45, 0.47))
# spectrum_plotter.plot_spectra(selected_value=4.0, bpm_list=["MQC1LE"], axis="y", freq_range=(0.45, 0.47))
# spectrum_plotter.plot_all_spectra(bpm_list=["MQC1LE"], axis="x")
# spectrum_plotter.plot_all_spectra(bpm_list=["MQC1LE"], axis="y")
spectrum_plotter.plot_spectra_grid(selected_value=4.0, bpm_list=["MQC2LE", "MQEAE16", "MQD3E14", "MQI5E"])


