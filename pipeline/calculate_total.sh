#!/bin/bash
# Path to the 'traces' directory
traces_dir="./traces"

# Check if directory exists
if [ ! -d "$traces_dir" ]; then
    echo "Directory not found: $traces_dir"
    exit 1
fi

declare -A traces_stats
declare -A algorithm_stats

# Loop through each item in the traces directory
printf "%-15s %-15s %-15s %-15s %-15s \n" "Program Name" "DR Trace" "DR Algo" "Trace Rate" "Algo Rate"
for item in "$traces_dir"/*; do
    if [ -d "$item" ]; then
        filecount=0
        dirname=$(basename "$item")
        traces_stats["$dirname"]=0
        algorithm_stats["$dirname"]=0
        for file in "$item"/*; do
            # Remove path and extract filename without extension
            filename=$(basename "$file")
            filename_without_ext="${filename%.*}"
            # Check if data race exists in trace
            if [ ! -f "./traces/$dirname/$filename_without_ext.csv" ]; then
              echo "File not found: ./traces/$dirname/$filename_without_ext.csv"
              exit 1
            fi
            data_race_in_trace=$(tail -n 1 "./traces/$dirname/$filename_without_ext.csv" | awk -F',' '{print $NF}')
            ((traces_stats["$dirname"]+=$data_race_in_trace))

            # Check if data race exists in execution
            if [ ! -f "./results/$dirname/$filename_without_ext.out" ]; then
              echo "File not found: ./results/$dirname/$filename_without_ext.out"
              exit 1
            fi
            data_race_in_algorithm=$(tail -n 1 "./results/$dirname/$filename_without_ext.out" | rev | cut -d' ' -f1 | rev)
            # echo $data_race_in_algorithm
            ((algorithm_stats["$dirname"]+=$data_race_in_algorithm>0))

        done
        LC_NUMERIC="C"
        num_files=$(find ./traces/$dirname -maxdepth 1 -type f | wc -l)
        trace_avg=$(echo "${traces_stats[$dirname]}/$num_files*100" | bc -l)
        algorithm_avg=$(echo "${algorithm_stats[$dirname]}/$num_files*100" | bc -l)
        printf "%-15s %-15d %-15d %-15.2f %-15.2f \n" $dirname "${traces_stats[$dirname]}" "${algorithm_stats[$dirname]}" $trace_avg $algorithm_avg
    elif [ -f "$item" ]; then
        echo "Error: File found in traces directory"
    fi
done
