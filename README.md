# C11 RA-race detection
This is a python tool to detect release-acquire data races in the C11 memory model.
## CSV trace format
The csv file is almost the same as the trace in cs11tester, except it does not have vector clocks. Also a new column called 'wval' is added that shows that value that is written in a rmw operation.

## Graph.py
This is the main script which will run our detection algorithm.
### Requirements
Requirements can be found in `requirements.txt` and installed via `pip install -r requirements.txt`.
Creating and using a venv is preferable as we are using a prerelease version of networkx.

### Usage
See `python Graph.py -h`

### Visualization
It is possible to get a visualization of the graph using the `--draw N` argument to draw the first `N` nodes or events.

## Pipeline running instructions
### Prerequisites
The script is guaranteed to run on a fresh instance of the vagrant VM from the c11tester artefact.
The script requires the [vagrant-scp](https://github.com/invernizzi/vagrant-scp) to be installed.
### Basic command usage
Before running the command it is recommended to make a backup of your VM files.
To generate the output of a program, make sure your working directory is `pipeline` then run:
```
./evaluate.sh -v <vm_dir_path> -i <program_path> -x <execution_count>
```
TODO: Add option for custom output directories
### File structure
- `/pipeline/results` - identified data races after running ./evaluate.sh
- `/pipeline/traces` - the traces used for identifying the data races
- `/pipeline/replacement_file` - files that need to be changed in the vagrant VM to allow custom number of executions/verbose output
### prep_vagrant.sh
The `prep_vagrant.sh` script is used to prepare the files in the vagrant VM for proper output when executing a program. In principle, this script has to be run only once per VM, as long as no changes are made to the ~/c11tester directory within the VM. Right now, it is run at the beggining of evaluate.sh, to avoid errors.
