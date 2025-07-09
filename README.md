# Final-Automation
This Python script, climate_data_app.py, processes climate data from multiple "stations" over a specific range of years (1981-2010). It's designed to read data from custom space-separated files, consolidate it, calculate averages, and fill missing data points in a "Trade" column (derived from the last station's data) using averages from other stations.
Here's a detailed breakdown:
User Input and Configuration:
Prompts the user to specify the number of climate stations.
Asks for names for each station.
The processing is fixed for years 1981 to 2010.
The base directory for climate data is set to C:\Users\aaa\Desktop\onelasttime.
File and Data Processing:
It iterates through each specified year and each station.
Filename Parsing: It extracts the year from filenames using a regex pattern like .XX (e.g., AS010319.92 for 1992, AS010319.05 for 2005). A heuristic is used to infer the century (19xx vs. 20xx).
Data Reading: It reads custom space-separated text files, specifically extracting the second column's data and coercing values to numeric, preserving NaN for non-numeric entries.
Data Consolidation: For each year, it combines data from all relevant files and stations into a single Pandas DataFrame.
'Trade' Column Calculation:
It adds a Day_of_Year column.
It calculates Average_Other_Stations by averaging data from all stations except the last one.
It creates a Trade column, initially a copy of the last station's data.
Crucially, if a value in the Trade column (from the last station) is missing (NaN), it's filled with the corresponding value from the Average_Other_Stations column. These filling operations are logged.
Mean Calculation: The mean of all data columns (excluding Day_of_Year) is calculated and appended as a "Mean" row to the processed DataFrame for each year.
Output:
Per-Year Excel Files: For each year, a file named processed_climate_data_[year].xlsx is saved in the base directory, containing the consolidated and processed data, including the 'Mean' row.
Per-Year Trade TXT Files: For each year, a file named trade_data_[year].txt is saved, containing only the Day_of_Year and Trade columns.
Final Formatted Excel File: A consolidated Excel file named [last_station_name]c.xlsx (e.g., 0730c.xlsx) is generated. This file contains a column for the last station's name, a 'Days' column, and columns for each processed year (1981-2010), populated with the Trade values.
Final Combined CSV: A combined CSV file named [num_years] best from [last_station_name] c.csv (e.g., 30 best from 1005 c.csv) is created. This file contains the 'Trade' data for all processed years, with 'Day' as the index.
Overall Trade Log TXT: A file named overall_trade_log.txt is created, detailing every instance where a NaN in the last station's data was filled with the Average_Other_Stations value.
Error Handling: The script includes checks for valid numerical inputs, existence of directories and files, correct file formats, and sufficient columns within data files.
