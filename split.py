#   This file is part of gem5-stats-parser-visualizer
# 
#   gem5-stats-parser-visualizer is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, version 3.
# 
#   gem5-stats-parser-visualizer is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with gem5-stats-parser-visualizer. If not, see <http://www.gnu.org/licenses/>.

import os
import re
import glob

# Regular expression pattern to match delimiter lines
pattern2 = re.compile(r'^-')

# Function to write lines to a file
def write_file(lines, index, prefix, directory):
    if lines:  # Only write if there are lines to write
        filename = os.path.join(directory, f"{prefix}{index:04d}")
        with open(filename, 'w') as f:
            f.writelines(lines)
        return filename
    return None

# Function to process each stats.txt file in the given directory
def process_directory(directory):
    input_file = os.path.join(directory, 'stats.txt')
    prefix = 'stats.roi.'

    # Check if stats.txt exists in the directory
    if not os.path.isfile(input_file):
        print(f"No stats.txt found in {directory}")
        return

    # Read the content of the input file
    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Initialize variables
    file_index = 0
    current_file_lines = []

    # Process lines and split the file based on the pattern
    for line in lines:
        if line.strip() == '':  # Skip empty or whitespace-only lines
            continue
        if pattern2.match(line):
            if current_file_lines:  # Write the current section only if it has content
                filename = write_file(current_file_lines, file_index, prefix, directory)
                if filename:
                    file_index += 1
                current_file_lines = []
        else:
            current_file_lines.append(line)

    # Write the last section if it has content
    if current_file_lines:
        write_file(current_file_lines, file_index, prefix, directory)

    print(f"Splitting completed for {directory}")

# Find all directories containing stats.txt
directories = [os.path.dirname(file) for file in glob.glob('*/stats.txt')]

# Loop through each directory and process stats.txt
for directory in directories:
    process_directory(directory)

