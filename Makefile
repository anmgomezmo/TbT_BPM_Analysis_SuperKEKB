# Makefile for creating file dictionary, creating output folders, modifying parameters and running SOMA

# Variables
PYTHON = python3
SCRIPT = generate_file_dict.py
INPUT_FOLDER =
OUTPUT_BASE = ./output
PARAMETERS_FILE = parameters.txt
MODEL_BASE = ./model

# Targets
.PHONY: all run_script create_output_folder create_model_folder modify_parameters run_code clean

all: run_script create_output_folder create_model_folder modify_parameters run_code

run_script:
	@if [ -z "$(INPUT_FOLDER)" ]; then \
		echo "Error: INPUT_FOLDER is not set. Use 'make INPUT_FOLDER=/path/to/input_folder'"; \
		exit 1; \
	fi
	@if [ ! -d "$(INPUT_FOLDER)" ]; then \
		echo "Error: INPUT_FOLDER does not exist or is not a directory."; \
		exit 1; \
	fi
	$(PYTHON) $(SCRIPT) $(INPUT_FOLDER)

create_output_folder:
	@if [ -z "$(INPUT_FOLDER)" ]; then \
		echo "Error: INPUT_FOLDER is not set. Use 'make INPUT_FOLDER=/path/to/input_folder'"; \
		exit 1; \
	fi
	@folder_name=$$(basename $(INPUT_FOLDER)); \
	mode=$$(echo $$folder_name | grep -oE '_HER_|_LER_' | tr -d '_'); \
	date_part=$$(echo $$folder_name | grep -oE '[0-9]{4}_[0-9]{2}_[0-9]{2}'); \
	if [ -z "$$mode" ] || [ -z "$$date_part" ]; then \
		echo "Error: Could not extract mode (HER/LER) or date from INPUT_FOLDER. Ensure the folder name contains _HER_ or _LER_ and a valid date in the format YYYY_MM_DD."; \
		exit 1; \
	fi; \
	output_folder="$(OUTPUT_BASE)/$$(echo $$folder_name | sed 's/^input_/output_/')"; \
	mkdir -p $$output_folder; \
	echo "Created output folder: $$output_folder"

create_model_folder:
	@if [ -z "$(INPUT_FOLDER)" ]; then \
		echo "Error: INPUT_FOLDER is not set. Use 'make INPUT_FOLDER=/path/to/input_folder'"; \
		exit 1; \
	fi
	@folder_name=$$(basename $(INPUT_FOLDER)); \
	mode=$$(echo $$folder_name | grep -oE '_HER_|_LER_' | tr -d '_'); \
	date_part=$$(echo $$folder_name | grep -oE '[0-9]{4}_[0-9]{2}_[0-9]{2}'); \
	if [ -z "$$mode" ] || [ -z "$$date_part" ]; then \
		echo "Error: Could not extract mode (HER/LER) or date from INPUT_FOLDER. Ensure the folder name contains _HER_ or _LER_ and a valid date in the format YYYY_MM_DD."; \
		exit 1; \
	fi; \
	model_folder="$(MODEL_BASE)/$$(echo $$folder_name | sed 's/^input_/model_/')"; \
	mkdir -p $$model_folder; \
	plain_file=$$(find $(INPUT_FOLDER) -type f \( -name "*_$$mode_*$$date_part*.sad" -o -name "*_$$mode_*$$date_part*.plain.sad" \) | head -n 1); \
	if [ -z "$$plain_file" ]; then \
		echo "Error: No .sad or .plain.sad file with _$$mode_ and $$date_part found in the input folder."; \
		exit 1; \
	fi; \
	cp $$plain_file $$model_folder/; \
	echo "Created model folder: $$model_folder and copied $$plain_file"

modify_parameters:
	@if [ -z "$(INPUT_FOLDER)" ]; then \
		echo "Error: INPUT_FOLDER is not set. Use 'make INPUT_FOLDER=/path/to/input_folder'"; \
		exit 1; \
	fi
	@folder_name=$$(basename $(INPUT_FOLDER)); \
	mode=$$(echo $$folder_name | grep -oE '_HER_|_LER_' | tr -d '_'); \
	date_part=$$(echo $$folder_name | grep -oE '[0-9]{4}_[0-9]{2}_[0-9]{2}'); \
	if [ -z "$$mode" ] || [ -z "$$date_part" ]; then \
		echo "Error: Could not extract mode (HER/LER) or date from INPUT_FOLDER. Ensure the folder name contains _HER_ or _LER_ and a valid date in the format YYYY_MM_DD."; \
		exit 1; \
	fi; \
	modified_file="parameters_$$(echo $$folder_name | sed 's/^input_//').txt"; \
	cp $(PARAMETERS_FILE) $$modified_file; \
	model_folder="$(MODEL_BASE)/$$(echo $$folder_name | sed 's/^input_/model_/')"; \
	plain_file=$$(find $$model_folder -type f \( -name "*_$$mode_*$$date_part*.sad" -o -name "*_$$mode_*$$date_part*.plain.sad" \) | head -n 1); \
	if [ -z "$$plain_file" ]; then \
		echo "Error: No .sad or .plain.sad file with _$$mode_ and $$date_part found in the model folder."; \
		exit 1; \
	fi; \
	file_dict="file_dict_$$(echo $$folder_name | sed 's/^input_//').txt"; \
	sed -i "s|^ringID = .*|ringID = $$mode|" $$modified_file; \
	sed -i "s|^lattice = .*|lattice = $$plain_file|" $$modified_file; \
	sed -i "s|^input_data_path = .*|input_data_path = ./$(INPUT_FOLDER)/|" $$modified_file; \
	sed -i "s|^model_path = .*|model_path = $$model_folder/|" $$modified_file; \
	output_folder="$(OUTPUT_BASE)/$$(echo $$folder_name | sed 's/^input_/output_/')"; \
	sed -i "s|^main_output_path = .*|main_output_path = $$output_folder/|" $$modified_file; \
	sed -i "s|^file_dict = .*|file_dict = ./$$file_dict|" $$modified_file; \
	echo "Modified parameters file saved as $$modified_file"

run_code:
	@if [ -z "$(INPUT_FOLDER)" ]; then \
		echo "Error: INPUT_FOLDER is not set. Use 'make INPUT_FOLDER=/path/to/input_folder'"; \
		exit 1; \
	fi
	@folder_name=$$(basename $(INPUT_FOLDER)); \
	mode=$$(echo $$folder_name | grep -oE '_HER_|_LER_' | tr -d '_'); \
	date_part=$$(echo $$folder_name | grep -oE '[0-9]{4}_[0-9]{2}_[0-9]{2}'); \
	if [ -z "$$mode" ] || [ -z "$$date_part" ]; then \
		echo "Error: Could not extract mode (HER/LER) or date from INPUT_FOLDER. Ensure the folder name contains _HER_ or _LER_ and a valid date in the format YYYY_MM_DD."; \
		exit 1; \
	fi; \
	parameters_file="parameters_$$(echo $$folder_name | sed 's/^input_//').txt"; \
	if [ ! -f "$$parameters_file" ]; then \
		echo "Error: Parameters file $$parameters_file does not exist. Run 'make modify_parameters' first."; \
		exit 1; \
	fi; \
	read -p "Do you want to run the code? (yes/no): " response; \
	if [ "$$response" = "yes" ]; then \
		read -p "Enter flags separated by spaces (or leave empty for no flags): " flags; \
		if [ -z "$$flags" ]; then \
			echo "Running without flags..."; \
			python3 run_SOMA.py --parameters $$parameters_file -omc3; \
		else \
			for flag in $$flags; do \
			echo "Running with flag $$flag..."; \
			python3 run_SOMA.py --parameters $$parameters_file $$flag -omc3; \
			done; \
		fi; \
	else \
		echo "Run canceled by the user."; \
	fi

clean:
	@rm -rf $(OUTPUT_BASE)
	@rm -rf $(MODEL_BASE)/model_*
	#@rm -f parameters_*.txt
	#@rm -f file_dict_*.txt
	@echo "Cleaned output directory, model folders, parameter files, and file dictionaries."