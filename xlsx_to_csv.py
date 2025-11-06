import pandas as pd
import sys
import os

def convert_xlsx_to_csv(input_file: str, output_file: str = None, sheet_name: str | int = 0):
    """
    Converts a single sheet from an XLSX file to a CSV file using pandas.

    Args:
        input_file (str): The path to the input .xlsx file.
        output_file (str, optional): The path for the output .csv file. 
                                     Defaults to the same name as the input file 
                                     but with a .csv extension.
        sheet_name (str | int, optional): The name or index (0-based) of the 
                                          sheet to convert. Defaults to the first sheet (0).
    """
    print(f"--- Starting conversion for: {input_file} ---")

    # 1. Determine the output filename if not provided
    if output_file is None:
        # Get the base name (e.g., 'data.xlsx' -> 'data')
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.csv"

    try:
        # 2. Read the Excel file into a pandas DataFrame
        # The engine='openpyxl' is explicitly included for robust .xlsx handling.
        print(f"Reading sheet '{sheet_name}' from Excel file...")
        df = pd.read_excel(input_file, sheet_name=sheet_name, engine='openpyxl')
        
        ## From column number 8 onwards are slots and they should be numbered from 1 to 67
        print(f"Converting to CSV and saving to: {output_file} ...")
        df.columns = [f"Slot {i-7}" if i >= 8 else col for i, col in enumerate(df.columns)]
        
        # 3. Write the DataFrame to a CSV file
        # index=False prevents writing the pandas row index as an extra column.
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        print(f"\n✅ Successfully converted to CSV.")
        print(f"Output saved to: {output_file}")

    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found at '{input_file}'")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ ERROR: Could not read sheet '{sheet_name}'. Details: {e}")
        print("Please check if the sheet name or index is correct.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure pandas is installed before proceeding
    try:
        import pandas as pd
    except ImportError:
        print("---")
        print("❌ pandas library not found.")
        print("Please install it using: pip install pandas openpyxl")
        print("---")
        sys.exit(1)

    # Check for correct number of command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python xlsx_to_csv.py <input_file.xlsx> [output_file.csv] [sheet_name_or_index]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Handle optional sheet name/index
    if len(sys.argv) > 3:
        sheet_input = sys.argv[3]
        try:
            # Try converting the argument to an integer (for index)
            sheet = int(sheet_input)
        except ValueError:
            # If it fails, treat it as a string (for sheet name)
            sheet = sheet_input
    else:
        sheet = 0 # Default to the first sheet
    
    convert_xlsx_to_csv(input_path, output_path, sheet)