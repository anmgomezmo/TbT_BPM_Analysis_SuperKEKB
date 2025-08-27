import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import logging
import tfs
import argparse

mpl.rcParams.update({
    'font.size': 16,
    "text.usetex": False,
    "font.family": "Arial"
})

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Class for plotting the comparison of spectras between simulation and experimental data
class SpectraComparison:
    def __init__(self, sim_base_path, exp_base_path):
        """
        Initialize with paths to both simulation and experimental data.
        
        Args:
            sim_base_path (str): Path to simulation data directory
            exp_base_path (str): Path to experimental data directory
        """
        self.sim_base_path = sim_base_path
        self.exp_base_path = exp_base_path
        self.output_path = os.path.join(os.path.dirname(sim_base_path), "plots")
        os.makedirs(self.output_path, exist_ok=True)
            
    def load_data(self, sim_date, exp_date, axis="x", bpm=None):
        """
        Load simulation and experimental data for comparison.
        
        Args:
            sim_date (str): Date identifier for simulation data
            exp_date (str): Date identifier for experimental data
            axis (str): 'x' or 'y' axis
            bpm (str): BPM name to analyze
                  
        Returns:
            tuple: Simulation and experimental data dictionaries
        """
        # Determine file extensions based on the axis
        amps_extension = "sdds.ampsx" if axis == "x" else "sdds.ampsy"
        freqs_extension = "sdds.freqsx" if axis == "x" else "sdds.freqsy"
            
        # Load simulation data
        sim_amps_file = os.path.join(self.sim_base_path, f"{sim_date}.{amps_extension}")
        sim_freqs_file = os.path.join(self.sim_base_path, f"{sim_date}.{freqs_extension}")

        # Load experimental data
        exp_amps_file = os.path.join(self.exp_base_path, f"{exp_date}.{amps_extension}")
        exp_freqs_file = os.path.join(self.exp_base_path, f"{exp_date}.{freqs_extension}")

        try:
            sim_amps_data = tfs.read_tfs(sim_amps_file)
            sim_freqs_data = tfs.read_tfs(sim_freqs_file)
            exp_amps_data = tfs.read_tfs(exp_amps_file)
            exp_freqs_data = tfs.read_tfs(exp_freqs_file)
                  
            # Ensure column names are stripped of whitespace
            sim_amps_data.columns = sim_amps_data.columns.str.strip()
            sim_freqs_data.columns = sim_freqs_data.columns.str.strip()
            exp_amps_data.columns = exp_amps_data.columns.str.strip()
            exp_freqs_data.columns = exp_freqs_data.columns.str.strip()
                  
            return {
                'sim': {
                    'amps': sim_amps_data,
                    'freqs': sim_freqs_data,
                    'date': sim_date
                },
                'exp': {
                    'amps': exp_amps_data,
                    'freqs': exp_freqs_data,
                    'date': exp_date
                }
            }
        except Exception as e:
            logging.error(f"Error reading data files: {e}")
            return None

    def find_max_in_range(self, freq_data, amp_data, freq_range=None):
        """
        Find the maximum amplitude and corresponding frequency, optionally within a specified range.
        
        Args:
            freq_data: DataFrame or Series with frequency values
            amp_data: DataFrame or Series with amplitude values
            freq_range: Tuple of (min_freq, max_freq) to search within, or None for entire range
            
        Returns:
            Tuple of (max_frequency, max_amplitude, max_index)
        """
        if freq_range:
            min_freq, max_freq = freq_range
            # Create mask for frequencies within the range
            mask = (freq_data >= min_freq) & (freq_data <= max_freq)
            # Apply mask to both frequency and amplitude data
            filtered_freq = freq_data[mask]
            filtered_amp = amp_data[mask]
            
            if len(filtered_amp) == 0:
                logging.warning(f"No data points found in frequency range {min_freq} to {max_freq}")
                return None, None, None
                
            # Find max in filtered data
            max_idx = np.argmax(filtered_amp)
            max_frequency = filtered_freq.iloc[max_idx]
            max_amplitude = filtered_amp.iloc[max_idx]
            
            # Get the original index from the unfiltered data
            original_indices = np.where(mask)[0]
            original_max_idx = original_indices[max_idx]
            
            return max_frequency, max_amplitude, original_max_idx
        else:
            # No range specified, find max in entire dataset
            max_idx = np.argmax(amp_data)
            max_frequency = freq_data.iloc[max_idx]
            max_amplitude = amp_data.iloc[max_idx]
            return max_frequency, max_amplitude, max_idx

    def compare_spectra(self, sim_date, exp_date, bpm_list=None, axis="x", freq_range=None, scaling=False):
        """
        Compare and plot spectra from simulation and experimental data.
        
        Args:
            sim_date (str): Date identifier for simulation data
            exp_date (str): Date identifier for experimental data
            bpm_list (list): List of BPMs to analyze, or None for all
            axis (str): 'x' or 'y' axis
            freq_range (tuple): Optional tuple of (min_freq, max_freq) to search for maximum
        """
        data = self.load_data(sim_date, exp_date, axis)
        if not data:
            logging.error("Failed to load required data.")
            return
        
        # Use the bpm_list or get all common BPMs between the datasets
        if not bpm_list:
            sim_bpms = set(data['sim']['amps'].columns)
            exp_bpms = set(data['exp']['amps'].columns)
            bpm_list = list(sim_bpms.intersection(exp_bpms))
        
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
        
        # Sort BPMs based on the desired order
        bpm_list = sorted(bpm_list, key=lambda x: bpm_order.index(x) if x in bpm_order else float('inf'))
        
        range_text = f"_{freq_range[0]}-{freq_range[1]}" if freq_range else ""
        pdf_filename = os.path.join(self.output_path, f"Spectra_Comparison_{axis.upper()}.pdf")
        with PdfPages(pdf_filename) as pdf:
            for bpm in bpm_list:
                if (bpm not in data['sim']['amps'].columns or bpm not in data['sim']['freqs'].columns or
                    bpm not in data['exp']['amps'].columns or bpm not in data['exp']['freqs'].columns):
                    logging.warning(f"BPM {bpm} not found in all datasets. Skipping.")
                    continue
                
                # Get simulation data
                sim_amp_data = data['sim']['amps'][bpm]
                sim_freq_data = data['sim']['freqs'][bpm]
                sim_max_frequency, sim_max_amplitude, _ = self.find_max_in_range(
                    sim_freq_data, sim_amp_data, freq_range
                )
                
                # Get experimental data
                exp_amp_data = data['exp']['amps'][bpm]
                exp_freq_data = data['exp']['freqs'][bpm]
                exp_max_frequency, exp_max_amplitude, _ = self.find_max_in_range(
                    exp_freq_data, exp_amp_data, freq_range
                )

                if scaling:
                  scaling_factor = exp_max_amplitude / sim_max_amplitude
                else:
                  scaling_factor = 1.0
                
                # Create plot
                fig, ax = plt.subplots(figsize=(12, 8))
                plt.yscale('log')
                
                # Plot simulation data
                ax.plot(sim_freq_data, sim_amp_data * scaling_factor, lw=1.5, color='blue', label=f"Simulation ({data['sim']['date']})")
                ax.fill_between(sim_freq_data, sim_amp_data * scaling_factor, color='blue', alpha=0.2)

                # Plot experimental data
                ax.plot(exp_freq_data, exp_amp_data, lw=1.5, color='red', label=f"Experimental ({data['exp']['date']})")
                ax.fill_between(exp_freq_data, exp_amp_data, color='red', alpha=0.2)
                
                # Add vertical lines at maximum amplitudes if found within range
                range_info = ""
                if freq_range:
                    min_freq, max_freq = freq_range
                    range_info = f" (Range: {min_freq:.4f}-{max_freq:.4f})"
                    
                    # Shade the frequency range area
                    ax.axvspan(min_freq, max_freq, alpha=0.1, color='green', 
                               #label=f"Analysis range {min_freq:.4f}-{max_freq:.4f}"
                               )
                
                # Add vertical lines for max values
                if sim_max_frequency is not None:
                    ax.axvline(x=sim_max_frequency, color='blue', linestyle='--', 
                              label=f"Sim Max @ {sim_max_frequency:.4f}")
                
                if exp_max_frequency is not None:
                    ax.axvline(x=exp_max_frequency, color='red', linestyle='--', 
                              label=f"Exp Max @ {exp_max_frequency:.4f}")
                
                # Set labels and title
                ax.set_xlabel('Fractional Tune')
                ax.set_ylabel('Amplitude [mm]')
                ax.set_title(f"BPM {bpm} - Simulation vs. Experimental")
                
                # Add grid and legend
                ax.grid(which='major', axis='x', linestyle=':', linewidth=0.7)
                ax.grid(which='both', axis='y', linestyle=':', linewidth=0.7)
                ax.minorticks_on()
                ax.legend(loc='best', fontsize='small')
                
                # Save the figure
                pdf.savefig(fig, dpi=150, bbox_inches='tight')
                plt.close(fig)
                
        logging.info(f"Comparison spectra plots saved in {pdf_filename}.")

# def main():
#     parser = argparse.ArgumentParser(description='Compare simulation and experimental spectral data')
#     parser.add_argument('--sim-path', required=True, help='Base path for simulation data')
#     parser.add_argument('--exp-path', required=True, help='Base path for experimental data')
#     parser.add_argument('--sim-date', required=True, help='Date identifier for simulation data')
#     parser.add_argument('--exp-date', required=True, help='Date identifier for experimental data')
#     parser.add_argument('--bpms', nargs='+', help='List of BPMs to analyze (default: all common BPMs)')
#     parser.add_argument('--axis', default='x', choices=['x', 'y'], help='Axis to analyze (x or y)')
#     parser.add_argument('--freq-min', type=float, help='Minimum frequency for finding maximum amplitude')
#     parser.add_argument('--freq-max', type=float, help='Maximum frequency for finding maximum amplitude')
    
#     args = parser.parse_args()
    
#     freq_range = None
#     if args.freq_min is not None and args.freq_max is not None:
#         freq_range = (args.freq_min, args.freq_max)
    
#     plotter = SpectraComparison(args.sim_path, args.exp_path)
#     plotter.compare_spectra(args.sim_date, args.exp_date, args.bpms, args.axis, freq_range)

# if __name__ == "__main__":
#     main()


# Example usage
sim_path = "/home/andym/Documents/SOMA/SOMA/output/output_track_scaled_HER_2024_06_17/synched_harmonic"
exp_path = "/home/andym/Documents/SOMA/SOMA/output/output_short_HER_2024_06_17/synched_harmonic"

comparison = SpectraComparison(sim_path, exp_path)
comparison.compare_spectra(
    sim_date="HER_2024_06_17_17_53_37",
    exp_date="HER_2024_06_17_17_53_37",
    bpm_list=["MQC2LE"],
    axis="y",
    freq_range=(0.45, 0.47),  # Find maximum within this frequency range
    scaling=True
)