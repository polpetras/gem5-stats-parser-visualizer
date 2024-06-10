# gem5-stats-parser-visualizer

gem5 stats parser and visualizer parses gem5 statistics (stats) files, and generates plots for statistics specified by the user.

## How to run

Sim folders should contain string `sim`. You can adjust this with `filter_str_list`.

### Step 1

    Adjust the input/input.csv file and select the stats you want to plot.

### Step 2

    Run split.py script. This script will break down stats.txt files in seperate ROI (Region of Interest) files. This script will generate files stats.roi.0000, stats.roi.0001, etc.

    A ROI is defined (enclosed) by:
    ```
    ---------- Begin Simulation Statistics ----------
    ...
    ---------- End Simulation Statistics   ----------
    ```
    In order to generate a ROI, user can use 
    - gem5_reset_stats(0,0) and
    - gem5_dump_stats(0,0) 
    inside his benchmark kernel code.


### Step 3

    Run gem5_parser.py script, to parse roi files and create the plots in output file graphs_out.pdf. By default the last ROI is ignored. Adjust ignore_last_roi if you want to plot that ROI also.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.


## Contact

If you have questions about this code, or need further help, contact polpetras AT gmail DOT com.
