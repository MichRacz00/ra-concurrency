#!/bin/bash
# Starting dir
ORIGINAL_DIR=$(pwd)
# Initialize variables
VM_DIR=""
PROGRAM_PATH=""
EXECUTION_COUNT=""

# Loop over arguments and process them
while getopts "v:i:x:h" opt; do
  case ${opt} in
    v ) # Process option for vm path
      VM_DIR=${OPTARG}
      ;;
    i ) # Process option for program path
      PROGRAM_PATH=${OPTARG}
      ;;
    x ) # Process option for number of executions of the program
      EXECUTION_COUNT=${OPTARG}
      ;;
    h ) # Show help
      echo "Usage: ./evaluate.sh -v <vm_dir_path> -i <program_path> -x <execution_count>"
      exit 0
      ;;
    \? ) # Handle unknown option
      echo "Usage: ./evaluate.sh -v <vm_dir_path> -i <program_path> -x <execution_count>"
      exit 1
      ;;
  esac
done

# Convert relative paths to absolute paths
VM_DIR=$(realpath "$VM_DIR")
PROGRAM_PATH=$(realpath "$PROGRAM_PATH")

# Update the files in the VM
# This can be commented out after first run of the script
./prep_vagrant.sh $VM_DIR

# Copy the program to vagrant VM
cd $VM_DIR
vagrant up
vagrant scp $PROGRAM_PATH default:~/temp_prog.cc

# Execute the program and generate the traces
vagrant ssh -c $"
cd ./c11tester
../c11tester-benchmarks/clang++ -lpthread ../temp_prog.cc
rm -rf ./csv
mkdir csv
export C11TESTER='-v3 -x ${EXECUTION_COUNT}'
export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:~/c11tester
./a.out
rm ./data.csv
exit
"

# Reset traces, results directories
rm -rf $ORIGINAL_DIR/results
rm -rf $ORIGINAL_DIR/traces

mkdir $ORIGINAL_DIR/results
mkdir $ORIGINAL_DIR/traces

# Copy the generated traces from vagrant VM
vagrant -r scp default:~/c11tester/csv/* ${ORIGINAL_DIR}/traces

# Remove the trace folder from vagrant VM to keep it clean
vagrant ssh -c "
cd ~/c11tester
rm -rf ./csv
exit
"
# Run the python script on all traces, piping the output
cd $ORIGINAL_DIR
for file in "./traces"/*; do
    # Check if it's a file (and not a directory)
    if [ -f "$file" ]; then
        # Print the filename
        filename=$(basename -- "$file")
        filename_without_extension="${filename%.*}"
        python3 ../src/Graph.py -i ./traces/$filename > ./results/$filename_without_extension.out
    fi
done

