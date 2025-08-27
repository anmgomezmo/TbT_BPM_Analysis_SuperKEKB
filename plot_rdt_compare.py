'''
Comparison of RDTs between experimental and simulation data
'''

import os
import logging
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    'font.size': 20,
    "text.usetex": False,
    "font.family": "Arial"
})

class RDTComparer:
    def __init__(self, exp_file, sim_file, output_path="."):
        self.exp_file = exp_file
        self.sim_file = sim_file
        self.output_path = output_path
        self.exp_data = None
        self.sim_data = None

    def _read_tfs(self, file_path):
        """Reads a .tfs file and returns a dict with S, AMP, ERRAMP lists."""
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            # Find column names and data start
            for i, line in enumerate(lines):
                if line.startswith('*'):
                    column_names = line.split()
                if line.startswith('$'):
                    data_start_index = i + 1
                    break

            # Extract data rows
            data = []
            for line in lines[data_start_index:]:
                if line.strip():
                    data.append(line.split())

            # Build dict
            data_dict = {col: [] for col in column_names[1:]}  # skip '*'
            for row in data:
                for col, value in zip(column_names[1:], row):
                    data_dict[col].append(value)

            # Convert to float
            s = list(map(float, data_dict["S"]))
            amp = list(map(float, data_dict["AMP"]))
            erramp = list(map(float, data_dict["ERRAMP"]))
            return {"S": s, "AMP": amp, "ERRAMP": erramp}
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            return None

    def read_data(self):
        """Reads both experimental and simulation data."""
        self.exp_data = self._read_tfs(self.exp_file)
        self.sim_data = self._read_tfs(self.sim_file)

    def plot_comparison(self, rdt, axis="y", label_exp="Experiment", label_sim="Simulation"):
        """
        Plots S vs AMP with error bars for both experiment and simulation.
        Args:
            rdt (str): e.g. "f1012"
            axis (str): "x" or "y"
        """
        if self.exp_data is None or self.sim_data is None:
            logging.error("Data not loaded. Call read_data() first.")
            return

        # RDT label
        rdt_numbers = [int(d) for d in rdt[1:]]
        rdt_sum = sum(rdt_numbers)
        power = 1 - (rdt_sum / 2)
        y_label = f"$|f_{{{''.join(map(str, rdt_numbers))},{axis}}}|$ [m$^{{{power:.0f}}}$]"

        plt.figure(figsize=(10, 6))
        plt.errorbar(self.exp_data["S"], self.exp_data["AMP"], yerr=self.exp_data["ERRAMP"],
                     fmt='o', linestyle='-', linewidth=1, label=label_exp, markersize=5, capsize=3, color='tab:blue')
        plt.errorbar(self.sim_data["S"], self.sim_data["AMP"], yerr=self.sim_data["ERRAMP"],
                     fmt='s', linestyle='--', linewidth=1, label=label_sim, markersize=5, capsize=3, color='tab:orange')

        plt.xlabel("Position [m]")
        plt.ylabel(y_label)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        # Save
        fname = f"compare_{rdt}_{axis.upper()}.pdf"
        out_path = os.path.join(self.output_path, fname)
        plt.savefig(out_path)
        plt.close()
        logging.info(f"Comparison plot saved as: {out_path}")

# Example usage:
comparer = RDTComparer("/home/andym/Documents/SOMA/SOMA/output/output_short_HER_2024_06_17/synched_optics/average/rdt/skew_octupole/f1012_y.tfs", 
                       "/home/andym/Documents/SOMA/SOMA/output/output_track_scaled_HER_2024_06_17/synched_optics/average/rdt/skew_octupole/f1012_y.tfs", 
                       output_path="/home/andym/Documents/SOMA/SOMA/output/output_track_scaled_HER_2024_06_17/plots")
comparer.read_data()
comparer.plot_comparison(rdt="f1012", axis="y")