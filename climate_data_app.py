import os
import re
import pandas as pd
import calendar
from tabulate import tabulate # For displaying tables in the console
import numpy as np # Added for np.nan

def extract_year_from_filename(filename):
    """
    Extracts the four-digit year from a filename like 'AS010319.92' or 'AS010319.92.txt'.
    Adjusts century inference (1900s vs 2000s) based on the two-digit year.
    """
    # Look for .XX pattern anywhere before an optional file extension
    match = re.search(r'\.(\d{2})(?:\.[^.]*)?$', filename, re.IGNORECASE)

    if match:
        two_digit_year = int(match.group(1))

        # Heuristic for century determination:
        # If the two-digit year is above 50 (e.g., 99, 86), assume 1900s.
        # If it's 50 or below (e.g., 00, 05, 24), assume 2000s.
        if two_digit_year > 50:
            full_year = 1900 + two_digit_year
        else:
            full_year = 2000 + two_digit_year
        
        return full_year
    return None # Return None if year pattern is not found

def read_custom_space_separated_file(filepath):
    """
    Attempts to read data from a custom space-separated text file,
    skipping the first column and extracting the second.
    This version PRESERVES all values from the 2nd column, including non-numeric ones.
    """
    try:
        # Use delim_whitespace=True for robust space-separated parsing.
        # header=None: assumes no header row.
        df = pd.read_csv(filepath, header=None, delim_whitespace=True)
        
        # Ensure there's a second column (index 1) to extract
        if df.shape[1] < 2:
            raise ValueError("File does not contain at least two columns after space-separation.")
            
        # Select the 2nd column (index 1).
        # We convert to numeric with errors='coerce' but DO NOT dropna() here.
        # This will turn truly non-numeric values into NaN, but keep the row.
        extracted_data = pd.to_numeric(df.iloc[:, 1], errors='coerce')
        
        print(f"    Successfully read as custom space-separated: {os.path.basename(filepath)}")
        return extracted_data # Return the series with NaNs if present

    except Exception as e:
        print(f"    Could not read {os.path.basename(filepath)} as custom space-separated: {e}. Skipping file.")
        return None

def run_climate_processor():
    # 1. User Input and Configuration
    while True:
        try:
            num_stations = int(input("How many stations? "))
            if num_stations <= 0:
                print("Please enter a positive number of stations.")
                continue
            break
        except ValueError:
            print("Invalid input! Please enter a valid integer for the number of stations.")

    station_names = [] # Initialize an empty list for station names
    print("\n--- Please name your stations ---")
    for i in range(num_stations):
        while True:
            name = input(f"Enter name for Station {i + 1}: ").strip()
            if name: # Ensure name is not empty
                station_names.append(name)
                break
            else:
                print("Station name cannot be empty. Please enter a valid name.")

    # Prepare data for tabulation
    table_data = [[i + 1, name] for i, name in enumerate(station_names)]
    headers = ["#", "Station Name"] # Initialize headers list

    print("\n--- Confirmed Stations ---")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print("--------------------------\n")

    # Automated year range from 1981 to 2010
    start_year = 1981
    end_year = 2010
    years_to_process = range(start_year, end_year + 1)

    # 2. Navigating Climate Data Directories
    base_path = r"C:\Users\aaa\Desktop\onelasttime" # CHANGED DIRECTORY

    # Verify base path existence
    if not os.path.isdir(base_path):
        print(f"Error: Base directory '{base_path}' not found. Please ensure the path is correct.")
        print("Exiting application.")
        return

    valid_station_paths = []
    print("\n--- Validating Station Folders ---")
    for station_name in station_names:
        station_folder_path = os.path.join(base_path, station_name)
        if os.path.isdir(station_folder_path):
            valid_station_paths.append(station_folder_path)
            print(f"Found folder for '{station_name}': {station_folder_path}")
        else:
            print(f"Warning: Folder for '{station_name}' not found at '{station_folder_path}'. Skipping.")

    if not valid_station_paths:
        print("No valid station folders found. Exiting application.")
        return

    # To store trade log for the final TXT file
    overall_trade_log = []

    # Dictionary to store 'Trade' column data for each year for the final CSV and new Excel
    # Key: year, Value: Pandas Series (Day_of_Year as index, Trade values)
    all_years_trade_data = {}

    for target_year in years_to_process:
        all_station_series = {} # Dictionary to hold Series for each station for the current year
        print(f"\n--- Processing data for year {target_year} ---")
        for station_path in valid_station_paths:
            station_name = os.path.basename(station_path)
            current_station_data_parts = [] # To hold data from multiple files for this station for the target year
            found_files_for_station_year = False # Flag to track if any relevant files were found

            for file_name in os.listdir(station_path):
                file_path = os.path.join(station_path, file_name)

                # Skip directories, process only files
                if os.path.isdir(file_path):
                    print(f"  - Skipping {file_name}: It's a directory.")
                    continue

                file_year = extract_year_from_filename(file_name)

                if file_year == target_year:
                    found_files_for_station_year = True # At least one relevant file found
                    print(f"  - Found file for target year ({file_year}): {file_name}. Attempting to read...")
                    extracted_data = read_custom_space_separated_file(file_path) # Call the specialized reader

                    if extracted_data is not None: # Check if reading was successful (even if it contains NaNs)
                        current_station_data_parts.append(extracted_data)
                    else:
                        print(f"    Failed to extract data from {file_name}. Skipping this file.")
                else:
                    if file_year is None:
                        print(f"  - Skipping file {file_name}: Year pattern (.XX) not found in filename.")
                    else:
                        print(f"  - Skipping file {file_name}: Detected year {file_year} does not match target year {target_year}.")

            if current_station_data_parts:
                # Concatenate all data parts found for this station for the target year
                combined_station_series = pd.concat(current_station_data_parts, ignore_index=True)
                all_station_series[f"{station_name}_Data"] = combined_station_series
            elif not found_files_for_station_year:
                print(f"  No files matching target year {target_year} were found for station '{station_name}'.")
            else: # Relevant files were found, but none yielded usable data
                print(f"  No valid data could be extracted from any files for station '{station_name}' for year {target_year}.")

        if not all_station_series:
            print(f"No data collected from any station for year {target_year}. Skipping to next year.")
            continue # Move to the next year

        # Consolidate all station data into a single DataFrame
        df_consolidated = pd.concat(all_station_series.values(), axis=1)
        df_consolidated.columns = all_station_series.keys() # Assign meaningful column names

        # 4. Processing Data (Add Day_of_Year Column and Handle Averages for Last Station)
        max_data_length = df_consolidated.shape[0] # Get current number of rows in consolidated data
        days_column = list(range(1, max_data_length + 1))

        df_processed = df_consolidated.copy()
        day_series = pd.Series(days_column, index=df_processed.index) # Create with matching index
        df_processed.insert(0, 'Day_of_Year', day_series)

        # Identify the last station column name
        last_station_col_name = None
        if len(station_names) > 0:
            last_station_col_name = f"{station_names[-1]}_Data"
        
        # Determine columns for 'Average_Other_Stations': all station data columns except the last one
        # Filter these to only include columns actually present in df_processed
        data_columns_for_average = []
        if len(station_names) > 1: # Need at least two stations for this logic to apply (1st to 2nd last)
            # Construct potential column names for averaging
            potential_avg_cols = [f"{name}_Data" for name in station_names[:-1]]
            # Filter to only include those actually present in df_processed
            data_columns_for_average = [col for col in potential_avg_cols if col in df_processed.columns]
        
        if data_columns_for_average:
            df_processed['Average_Other_Stations'] = df_processed[data_columns_for_average].mean(axis=1)
            print(f"Created 'Average_Other_Stations' column (average of {', '.join([col.replace('_Data', '') for col in data_columns_for_average])}).")
        else:
            df_processed['Average_Other_Stations'] = np.nan # Assign np.nan if no columns to average
            print("Not enough valid station data columns (excluding the last one) to calculate 'Average_Other_Stations'.")

        # Create 'Trade' column: copy last station data, then fill NaNs with 'Average_Other_Stations'
        # Initialize 'Trade' column. If last_station_col_name doesn't exist or is empty, it will be all NaN.
        # FIX: Use np.nan instead of pd.NA for float dtype compatibility
        df_processed['Trade'] = df_processed[last_station_col_name].copy() if last_station_col_name and last_station_col_name in df_processed.columns else pd.Series([np.nan] * max_data_length, dtype=float)

        current_year_trades = [] # To log trades for this specific year
        if last_station_col_name and last_station_col_name in df_processed.columns and 'Average_Other_Stations' in df_processed.columns:
            print(f"Checking for gaps in '{last_station_col_name}' and filling 'Trade' column with 'Average_Other_Stations' if needed.")
            for index, row in df_processed.iterrows():
                # Check if 'Trade' column has NaN AND 'Average_Other_Stations' has a valid number
                if pd.isna(row['Trade']) and pd.notna(row['Average_Other_Stations']):
                    original_value = row[last_station_col_name] # This will be NaN
                    new_value = row['Average_Other_Stations']
                    df_processed.at[index, 'Trade'] = new_value
                    current_year_trades.append(
                        f"Year: {target_year}, Day: {int(row['Day_of_Year'])} - Filled '{last_station_col_name}' (Original: {original_value}) with Average_Other_Stations: {new_value:.2f}"
                    )
        overall_trade_log.extend(current_year_trades) # Add this year's trades to the overall log

        # Store 'Trade' column data for the final CSV and new Excel
        # Use Day_of_Year as index for alignment later. Ensure 'Trade' column is numeric.
        if 'Trade' in df_processed.columns:
            all_years_trade_data[target_year] = df_processed[['Day_of_Year', 'Trade']].set_index('Day_of_Year')['Trade']
        else:
            all_years_trade_data[target_year] = pd.Series(dtype=float) # Store an empty series if 'Trade' column wasn't created

        # 5. Calculating and Appending Column Means (for df_final)
        # Include 'Trade' and 'Average_Other_Stations' in the final mean calculation
        final_mean_cols = [col for col in df_processed.columns if col not in ['Day_of_Year']] # All data columns including new ones
        
        column_means = df_processed[final_mean_cols].mean(axis=0)

        # Prepare the mean row for appending
        mean_row_series = pd.Series(dtype=object)
        mean_row_series['Day_of_Year'] = "Mean"
        for col, mean_val in column_means.items():
            mean_row_series[col] = mean_val
        
        # Append the mean row to the DataFrame
        df_final = pd.concat([df_processed, pd.DataFrame([mean_row_series])], ignore_index=True)

        # 6. Exporting Processed Data to Excel (per year)
        output_excel_filename = f"processed_climate_data_{target_year}.xlsx"
        output_excel_path = os.path.join(base_path, output_excel_filename)
        
        try:
            df_final.to_excel(output_excel_path, index=False)
            print(f"Processed data for year {target_year} successfully saved to: {output_excel_path}")
        except Exception as e:
            print(f"Error saving processed data for year {target_year} to {output_excel_path}: {e}")

        # 7. Create per-year TXT file with Day and Trade columns
        output_txt_filename = f"trade_data_{target_year}.txt"
        output_txt_path = os.path.join(base_path, output_txt_filename)
        try:
            # Ensure 'Trade' column exists and is not empty before trying to save
            if 'Trade' in df_processed.columns and not df_processed['Trade'].empty:
                # Remove the 'Mean' row before saving to TXT if it's not needed for day-wise data
                df_for_txt = df_processed[df_processed['Day_of_Year'] != 'Mean'][['Day_of_Year', 'Trade']]
                df_for_txt.to_csv(output_txt_path, sep='\t', index=False, header=True) # Use tab for separation, include header
                print(f"Trade data for year {target_year} saved to: {output_txt_path}")
            else:
                print(f"Skipping TXT output for year {target_year}: 'Trade' column not found or is empty.")
        except Exception as e:
            print(f"Error saving trade data for year {target_year} to {output_txt_path}: {e}")

    # --- New: Final Formatted Excel File Generation ---
    if all_years_trade_data and len(station_names) > 0:
        print("\n--- Generating Final Formatted Excel File ---")
        last_station_full_name = station_names[-1] # e.g., '0730'
        
        # Create DataFrame from collected 'Trade' data
        df_new_format_excel = pd.DataFrame(all_years_trade_data)
        
        # Reset index to make Day_of_Year a column
        df_new_format_excel = df_new_format_excel.reset_index()
        
        # Rename 'index' column to 'Days'
        df_new_format_excel = df_new_format_excel.rename(columns={'Day_of_Year': 'Days'})
        
        # Add the 'Station Name' column as the very first column
        station_numeric_name = last_station_full_name # Assuming station_names are already numeric or the desired identifier
        df_new_format_excel.insert(0, station_numeric_name, station_numeric_name) # Column header is the station name itself
        
        # The columns are already named by year (e.g., 1981, 1982) from all_years_trade_data keys, no need to rename.
        
        # Construct output path
        output_new_excel_filename = f"{station_numeric_name}c.xlsx"
        output_new_excel_path = os.path.join(base_path, output_new_excel_filename)
        
        try:
            df_new_format_excel.to_excel(output_new_excel_path, index=False)
            print(f"Final formatted Excel file saved to: {output_new_excel_path}")
        except Exception as e:
            print(f"Error saving final formatted Excel file to {output_new_excel_path}: {e}")
    else:
        print("\nNo 'Trade' data collected across any year or no stations provided, skipping final formatted Excel generation.")

    # Final CSV for the 'Trade' column (which is derived from the last station)
    # This block now ensures the CSV is created with the specified naming convention
    if all_years_trade_data and len(station_names) > 0:
        print("\n--- Final Combined CSV Generation ---")
        num_years_processed = len(years_to_process) # This will be 30 (2010 - 1981 + 1)
        last_station_identifier = station_names[-1] # This gets the last name entered by the user

        # Construct the exact filename as requested
        # Example: "30 best from 1005c.csv"
        final_csv_filename = f"{num_years_processed} best from {last_station_identifier} c.csv"
        final_csv_path = os.path.join(base_path, final_csv_filename)
        
        # Consolidate into a single DataFrame for the final CSV
        df_final_csv = pd.DataFrame(all_years_trade_data)
        df_final_csv.index.name = 'Day' # Rename index for clarity
        # Columns are already years (e.g., 1981, 1982, etc.), no need to prepend 'Year_'
        
        try:
            df_final_csv.to_csv(final_csv_path, index=True) # Write index (Day)
            print(f"\nSuccessfully generated the combined CSV file:")
            print(f"  Filename: {final_csv_filename}")
            print(f"  Location: {final_csv_path}")
            print(f"Please check the directory: {base_path}")
        except Exception as e:
            print(f"\nError saving final combined CSV to {final_csv_path}: {e}")
    else:
        print("\nNo data processed across any year or no stations provided, skipping final combined CSV generation.")

    # Create the overall trade log TXT file
    trade_log_filename = "overall_trade_log.txt"
    trade_log_path = os.path.join(base_path, trade_log_filename)
    try:
        with open(trade_log_path, 'w') as f:
            f.write("Overall Trade Log for Climate Data Processing (1981-2010)\n")
            f.write("----------------------------------------------------------\n\n")
            if overall_trade_log:
                for entry in overall_trade_log:
                    f.write(entry + "\n")
            else:
                f.write("No 'trade' operations (filling of last station's gaps) occurred across all years.\n")
        print(f"\nOverall trade log successfully saved to: {trade_log_path}")
    except Exception as e:
        print(f"\nError saving overall trade log to {trade_log_path}: {e}")


if __name__ == "__main__":
    run_climate_processor()
