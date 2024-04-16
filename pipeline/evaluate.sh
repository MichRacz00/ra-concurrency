#!/bin/bash
# Starting dir
ORIGINAL_DIR=$(pwd)
# Initialize variables
VM_DIR=""
PROGRAM_PATH=""
EXECUTION_COUNT=""
SAVE_DIR=""
VM_INPUT=0

# Loop over arguments and process them
while getopts "v:i:x:h:m" opt; do
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
    m ) # Flag for whether to use VM path
      VM_INPUT=1
      ;;
    h ) # Show help
      echo "Usage: ./evaluate.sh -v <vm_dir_path> -i <program_path> -x <execution_count> -m <vm_path>"
      exit 0
      ;;
    \? ) # Handle unknown option
      echo "Usage: ./evaluate.sh -v <vm_dir_path> -i <program_path> -x <execution_count>"
      exit 1
      ;;
  esac
done

SAVE_DIR="${PROGRAM_PATH##*/}"
echo $SAVE_DIR
# Convert relative paths to absolute paths
VM_DIR=$(realpath "$VM_DIR")
if [ $VM_INPUT -eq 0 ]; then
PROGRAM_PATH=$(realpath "$PROGRAM_PATH")
fi
# Update the files in the VM
# This can be commented out after first run of the script
./prep_vagrant.sh $VM_DIR


# Copy the program to vagrant VM
echo VM_INPUT
cd $VM_DIR
vagrant up
if [ $VM_INPUT -eq 0 ]; then
vagrant scp $PROGRAM_PATH default:~/temp_prog.cc
fi

# Execute the program and generate the traces
if [ $VM_INPUT -eq 0 ]; then
vagrant ssh -c $"
cd ./c11tester
../c11tester-benchmarks/clang++ -lpthread ../temp_prog.cc
rm -rf ./csv
mkdir csv
export C11TESTER='-v3 -x1'
export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:~/c11tester
for ((i=1; i<=${EXECUTION_COUNT}; i++))
do
    ./a.out
    rm ./data.csv
done
exit
"
fi

if [ $VM_INPUT -eq 1 ]; then
vagrant ssh -c $"
cd ./c11tester
rm -rf ./csv
mkdir csv
export CDSLIB='/home/vagrant/c11tester'
export C11TESTER='-v3 -x1'
export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:~/c11tester
for ((i=1; i<=${EXECUTION_COUNT}; i++))
do
    ~${PROGRAM_PATH}
    rm ./data.csv
done
exit
"
fi

# Reset traces, results directories
rm -rf $ORIGINAL_DIR/results/$SAVE_DIR
rm -rf $ORIGINAL_DIR/traces/$SAVE_DIR

mkdir $ORIGINAL_DIR/results/$SAVE_DIR
mkdir $ORIGINAL_DIR/traces/$SAVE_DIR

# Copy the generated traces from vagrant VM
vagrant -r scp default:~/c11tester/csv/* ${ORIGINAL_DIR}/traces/$SAVE_DIR

# Remove the trace folder from vagrant VM to keep it clean
vagrant ssh -c "
cd ~/c11tester
rm -rf ./csv
exit
"
# Run the python script on all traces, piping the output
cd $ORIGINAL_DIR
for file in "./traces/$SAVE_DIR"/*; do
    # Check if it's a file (and not a directory)
    if [ -f "$file" ]; then
        # Print the filename
        filename=$(basename -- "$file")
        filename_without_extension="${filename%.*}"
        python3 ../src/Graph.py -i ./traces/$SAVE_DIR/$filename > ./results/$SAVE_DIR/$filename_without_extension.out
    fi
done

