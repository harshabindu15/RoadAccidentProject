import pandas as pd

file_path = "dataset/road_accident_two_tables_sample_2011_to_2026.xlsx"

excel_file = pd.ExcelFile(file_path)

print("Available sheets:", excel_file.sheet_names)

for sheet in excel_file.sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet)

    print("\n==============================")
    print("Sheet:", sheet)
    print("Columns:", df.columns.tolist())
    print("Total rows:", len(df))
    print("==============================")

    print(df.head(3).to_string(index=False))