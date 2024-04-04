# C11 RA-race detection
This is a python tool to detect release-acquire data races in the C11 memory model.
## CSV trace format
The csv file is almost the same as the trace in cs11tester, except it does not have vector clocks. Also a new column called 'wval' is added that shows that value that is written in a rmw operation.

## Requirements
Requirements can be found in `requirements.txt` and installed via `pip install -r requirements.txt`.
Creating and using a venv is preferable as we are using a prerelease version of networkx.

## Visualization
It is possible to get a visualization of the graph using the `--draw N` argument to draw the first `N` nodes or events.
