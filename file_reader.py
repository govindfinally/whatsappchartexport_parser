import pandas as pd
from arrlenhandling import lenhandling
import os
import re
from typing import Optional


# ==============================
#        EXCEL CLEANER
# ==============================

class excelcleaner:

    @staticmethod
    def filecleaner(dataframe: pd.DataFrame, newfilename: Optional[str] = None) -> pd.DataFrame:
        df = dataframe.copy()
        df = df.dropna(how="all")

        if newfilename:
            df.to_excel(newfilename, index=False, engine="openpyxl")

        return excelcleaner.filecleaner_advanced(df)

    @staticmethod
    def filecleaner_advanced(dataframe: pd.DataFrame) -> pd.DataFrame:
        df = dataframe.copy()

        if "Application Link" in df.columns:
            df = df.drop(columns=["Application Link"])

        for col in ["Job Role", "CTC"]:
            if col not in df.columns:
                df[col] = pd.NA

        mask_both_missing = df["Job Role"].isna() & df["CTC"].isna()
        df = df.loc[~mask_both_missing].reset_index(drop=True)

        str_cols = df.select_dtypes(include=["object"]).columns
        for c in str_cols:
            df[c] = df[c].astype(str).str.strip()

        return df


# ==============================
#        FILE READER
# ==============================

class FileReader:

    def __init__(self):
        self.keys_ = [
            "Job Role", "CTC", "Stipend", "Eligible Batch",
            "Eligible Courses", "Eligible Branches",
            "Internship Duration", "Location", "Application Link"
        ]

        self.company_dict = {
            "name": [],
            "Job Role": [],
            "CTC": [],
            "Stipend": [],
            "Eligible Batch": [],
            "Eligible Courses": [],
            "Eligible Branches": [],
            "Internship Duration": [],
            "Location": [],
            "Application Link": []
        }

    # ==============================
    #  COMPANY NAME EXTRACTOR
    # ==============================

    def extract_company_name(self, header_line):
        line = header_line.replace('\u200e', '').replace('\u202f', '').strip()

        # Remove [date time] part (new format)
        if line.startswith("["):
            line = re.sub(r'^\[.*?\]\s+', '', line)

        # Remove old format date prefix
        else:
            line = re.sub(r'^\d{2}/\d{2}/\d{2},.*?\-\s+', '', line)

        # Remove sender name
        parts = line.split(":", 1)
        content = parts[1].strip() if len(parts) > 1 else line.strip()

        # Extract before "|"
        company_name = content.split("|")[0].strip("* ").strip()

        return company_name

    # ==============================
    #  KEY NORMALIZER
    # ==============================

    def normalize_key(self, line):
        clean_line = line.strip('*').strip()
        line_lower = clean_line.lower()

        for key in self.keys_:
            if line_lower.startswith(key.lower() + ":"):
                return key

        variations = {
            "eligible batches:": "Eligible Batch",
            "eligible course:": "Eligible Courses",
            "eligible branch:": "Eligible Branches",
            "application form:": "Application Link",
            "registration link:": "Application Link",
            "ctc (on ppo conversion):": "CTC",
            "role:": "Job Role",
            "job title:": "Job Role",
            "job role:": "Job Role",
            "stipend offered:": "Stipend",
            "duration:": "Internship Duration"
        }

        for variation, normalized_key in variations.items():
            if line_lower.startswith(variation):
                return normalized_key

        return None

    # ==============================
    #  MAIN PROCESSOR
    # ==============================

    def process_content(self, content: str, verbose=False):

        lines = content.split('\n')

        # Reset dict
        self.company_dict = {key: [] for key in self.company_dict.keys()}

        i = 0
        company_count = 0
        processing_log = []

        while i < len(lines):
            raw_line = lines[i]
            line = raw_line.replace('\u200e', '').replace('\u202f', '').strip()

            if not line:
                i += 1
                continue

            # MATCH BOTH OLD + NEW FORMATS
            header_pattern = r'^\[?\d{2}/\d{2}/\d{2},.*?\]?\s+.*?:'

            if re.match(header_pattern, line) and "|" in line:

                company_name = self.extract_company_name(line)

                if not company_name:
                    i += 1
                    continue

                company_count += 1

                if verbose:
                    processing_log.append(f"COMPANY #{company_count}: {company_name}")

                temp_dict = {key: "" for key in self.company_dict.keys()}
                temp_dict["name"] = company_name

                i += 1
                current_key = None
                current_value = []

                while i < len(lines):
                    next_line = lines[i].replace('\u200e', '').replace('\u202f', '').strip()

                    if re.match(header_pattern, next_line):
                        break

                    if not next_line:
                        i += 1
                        continue

                    matched_key = self.normalize_key(next_line)

                    if matched_key:
                        if current_key:
                            temp_dict[current_key] = " | ".join(current_value)

                        current_key = matched_key
                        value_part = next_line.strip('*').split(":", 1)
                        current_value = [value_part[1].strip()] if len(value_part) > 1 else []

                    elif current_key:
                        clean_line = next_line.lstrip('*').lstrip('•').lstrip('-').strip()
                        if clean_line:
                            current_value.append(clean_line)

                    i += 1

                if current_key:
                    temp_dict[current_key] = " | ".join(current_value)

                for key in self.company_dict.keys():
                    self.company_dict[key].append(temp_dict[key])

                continue

            i += 1

        if verbose:
            processing_log.append(f"TOTAL COMPANIES FOUND: {company_count}")

        handler = lenhandling()
        self.company_dict = handler.lenhandling(self.company_dict)

        df = pd.DataFrame.from_dict(self.company_dict)

        if verbose:
            return df, processing_log

        return df

    # ==============================
    # CLI METHOD
    # ==============================

    def dictupdate(self, filename: str):

        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()

        df, log = self.process_content(content, verbose=True)

        for line in log:
            print(line)

        print("\nDataFrame Preview:")
        print(df.to_string())

        newfilename = input("\nEnter the filename to save the excel (without .xlsx extension): ")
        newfilename_path = os.path.join(os.getcwd(), newfilename + ".xlsx")

        print(f"Saving to: {newfilename_path}")

        excel_cleaner = excelcleaner()
        cleaned_df = excel_cleaner.filecleaner(df, newfilename_path)

        print("Dictionary update completed.")

        return cleaned_df


# ==============================
#  MAIN
# ==============================

if __name__ == "__main__":
    try:
        file_reader = FileReader()
        chat_text = r"D:\chatexport\tester.txt"
        file_reader.dictupdate(chat_text)

    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()

    finally:
        print("Execution completed.")
