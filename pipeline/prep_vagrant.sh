#!/bin/bash
# The path to the VM directory is the first argument
ORIGINAL_DIR=$(pwd)
VM_DIR=$(realpath "$1")

cd $VM_DIR
vagrant up

vagrant scp $ORIGINAL_DIR/replacement_files/action.cc default:~/c11tester/action.cc
vagrant scp $ORIGINAL_DIR/replacement_files/execution.cc default:~/c11tester/execution.cc
vagrant scp $ORIGINAL_DIR/replacement_files/model.cc default:~/c11tester/model.cc
vagrant scp $ORIGINAL_DIR/replacement_files/datarace.cc default:~/c11tester/datarace.cc
vagrant ssh -c $'
cd ./c11tester
make
exit'

exit