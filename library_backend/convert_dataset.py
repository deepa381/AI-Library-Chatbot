import os
import pandas as pd

dataset_dir = r"c:\Users\csven\Downloads\library chatbot\library_backend\dataset"

csv_files = [f for f in os.listdir(dataset_dir) if f.endswith(".csv")]

print(f"Found {len(csv_files)} CSV files in {dataset_dir}")

for csv_file in csv_files:
    csv_path = os.path.join(dataset_dir, csv_file)
    xlsx_file = csv_file.replace(".csv", ".xlsx")
    xlsx_path = os.path.join(dataset_dir, xlsx_file)
    
    print(f"Converting {csv_file} to {xlsx_file}...")
    df = pd.read_csv(csv_path)
    df.to_excel(xlsx_path, index=False)

print("Conversion complete!")
