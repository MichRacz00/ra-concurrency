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
output=$(printf "%-15s %-15s %-15s %-15s %-15s %-15s %-15s \n" "Program Name" "DR Trace" "DR Algo" "Trace Rate" "Algo Rate" "Elapsed time" "Avg lines in trace")
output+=$'\n' 
for item in "$traces_dir"/*; do
    LC_NUMERIC="C"
    if [ -d "$item" ]; then
        filecount=0
        echo $item
        echo $(basename "$item")
        dirname=$(basename "$item")
        
        traces_stats["${dirname//./_}"]=0
        algorithm_stats["${dirname//./_}"]=0
        elapsed_time["${dirname//./_}"]=0
        trace_line_count["${dirname//./_}"]=0
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
            ((traces_stats["${dirname//./_}"]+=$data_race_in_trace))

            # Check if data race exists in execution
            if [ ! -f "./results/$dirname/$filename_without_ext.out" ]; then
              echo "File not found: ./results/$dirname/$filename_without_ext.out"
              exit 1
            fi
            ((trace_line_count["${dirname//./_}"]+=$(wc -l < ./traces/$dirname/$filename_without_ext.csv)))
            data_race_in_algorithm=$(tail -n 2 "./results/$dirname/$filename_without_ext.out" | head -n 1 | awk '{print $NF}')
            # echo $data_race_in_algorithm 
            if (( data_race_in_algorithm > 0 )); then
                data_race_in_algorithm=1
            fi
            ((algorithm_stats["${dirname//./_}"]+=$data_race_in_algorithm))
            if [ "$data_race_in_algorithm" -ne "$data_race_in_trace" ]; then
                echo "Data race mistmatch in $dirname for execution $filename_without_ext"
            fi
            elapsed_time["${dirname//./_}"]=$(echo "${elapsed_time["${dirname//./_}"]} + $(tail -n 1 "./results/$dirname/$filename_without_ext.out" | head -n 1 | awk '{print $NF}')" | bc)
        done
        
        num_files=$(find ./traces/$dirname -maxdepth 1 -type f | wc -l)
        trace_avg=$(echo "${traces_stats["${dirname//./_}"]}/$num_files*100" | bc )
        algorithm_avg=$(echo "${algorithm_stats["${dirname//./_}"]}/$num_files*100" | bc -l)
        avg_elapsed_time=$(echo "${elapsed_time["${dirname//./_}"]}/$num_files" | bc -l)
        avg_trace_count=$(echo "${trace_line_count["${dirname//./_}"]}/$num_files" | bc -l)
        output+=$(printf "%-15s %-15d %-15d %-15.2f %-15.2f %-15.6f %-15.2f\n" $dirname "${traces_stats["${dirname//./_}"]}" "${algorithm_stats["${dirname//./_}"]}" $trace_avg $algorithm_avg $avg_elapsed_time $avg_trace_count)
        output+=$'\n' 
    elif [ -f "$item" ]; then
        echo "Error: File found in traces directory"
    fi
done
printf "\n"
echo "$output"
