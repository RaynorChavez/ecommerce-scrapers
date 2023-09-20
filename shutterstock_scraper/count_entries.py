import os
import csv

def count_csv_entries(folder_path):
    total_entries = 0
    file_count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            filepath = os.path.join(folder_path, filename)
            file_count += 1
            with open(filepath, 'r') as csvfile:
                csvreader = csv.reader(csvfile)
                row_count = sum(1 for row in csvreader) - 1  # Exclude header
                print(f"Number of entries in {filename}: {row_count}")
                total_entries += row_count
    print(f"Total number of CSV files: {file_count}")
    print(f"Total number of entries across all CSV files: {total_entries}")

# Replace 'your_folder_path_here' with the path to the folder containing the CSV files
count_csv_entries('./')
