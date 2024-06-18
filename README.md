# gem5-stats-parser-visualizer

gem5 stats parser and visualizer parses gem5 statistics (stats) files, and generates plots for statistics specified by the user.

## How to run

Sim folders should contain string `sim`. You can adjust this with `filter_str_list`.

### Step 1

Adjust the `input/input.csv` file and select the stats you want to plot.

### Step 2

Run `split.py` script. This script will break down stats.txt files in seperate ROI (Region of Interest) files. This script will generate files `stats.roi.0000`, `stats.roi.0001`, etc.

A ROI is defined (enclosed) by:

```
---------- Begin Simulation Statistics ----------
...
---------- End Simulation Statistics   ----------
```

In order to generate a ROI, user can use:
```
    #include <m5ops.h>
    ...
    gem5_reset_stats(0,0)
    ROI_Kernel_code() <-- code for which we need statistics
    gem5_dump_stats(0,0)
    ...
```
inside the benchmark code.

User can specify a filter substring for the simulation directories (e.g. `sim`). All other directories are ignored. To adjust this substring edit:
`filter_str_list = [ 'sim' ]` in `gem5_parser.py`

### Step 3

    Run gem5_parser.py script, to parse ROI files and create the plots in output file graphs_out.pdf. By default the last ROI is ignored. Adjust ignore_last_roi if you want to plot that ROI also.

## Complex expressions in statistics input

This software allows for complex expressions in the statistics input (`input/input.csv`):

### 1. Component ID ranges

If you want to plot one statistic for several controllers you can specify a range using brackets, e.g.
for ploting avg QLat for controllers 0 to 7:

```
system.mem_ctrls[0-7].dram.avgQLat,value,Average queueing delay per DRAM burst,
```

### 2. Ratio of one statistic vs another

One can specify:
```
system.ruby.network.router_flit_queueing_latency /system.ruby.network.router_flits_received ,value, Queue Latency (ticks),
```
as input, in order to calculate the flit queueing latency per flit.

### 3. Units conversion

Additionally, if one wants to convert one unit to another, one can specify a numeric value in the fourth column of `input.csv`, e.g.:
```
system.mem_ctrls[7-8].avgWrBWSys,value,Average system write bandwidth in MByte/s,1000000
```

By default avgWrBWSys is expressed in Bytes/s. In order to convert it to MB/s, one can specify `1000000`, in the last column, which makes the parser
to divide the avgWrBWSys stat value by `1000000`.

Another conversion example is converting ticks (picoseconds) to cycles by dividing with 500 (For a 2GHz NoC clock), e.g.:
```
system.ruby.network.average_packet_vqueue_latency ,value,Queue Latency (Cycles),500
```

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.


## Contact

If you have questions about this code, or need further help, contact polpetras AT gmail DOT com.
