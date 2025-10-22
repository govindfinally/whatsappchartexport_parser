import pandas as pd
from arrlenhandling import lenhandling
import os
import re

class excelcleaner:
    @staticmethod
    def filecleaner(dataframe, newfilename: str):
        df = dataframe
        df = df.dropna(how='all')
        print(df.info())
        df.to_excel(newfilename, index=False, engine='openpyxl')

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

    def extract_company_name(self, header_line):
        """Extract company name from header line"""
        # Remove date/phone prefix
        clean_line = re.sub(r'^\d{2}/\d{2}/\d{2},\s+\d{2}:\d{2}\s+-\s+\+[\d\s]+:\s+', '', header_line)
        clean_line = clean_line.strip('*').strip()
        
        # Get first part before |
        parts = clean_line.split('|')
        company_name = parts[0].strip() if parts else ""
        
        return company_name

    def normalize_key(self, line):
        """Check if line starts with any of our keys (including variations)"""
        # Remove leading/trailing asterisks and whitespace
        clean_line = line.strip('*').strip()
        line_lower = clean_line.lower()
        
        # Direct matches
        for key in self.keys_:
            if line_lower.startswith(key.lower() + ":"):
                return key
        
        # Handle variations
        variations = {
            "eligible batches:": "Eligible Batch",
            "eligible course:": "Eligible Courses",
            "eligible branch:": "Eligible Branches",
            "application form:": "Application Link",
            "ctc (on ppo conversion):": "CTC"
        }
        
        for variation, normalized_key in variations.items():
            if line_lower.startswith(variation):
                return normalized_key
        
        return None

    def dictupdate(self, filename: str):
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.readlines()
        
        i = 0
        company_count = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check if this is a company header (has date/phone prefix and contains | )
            if re.match(r'^\d{2}/\d{2}/\d{2},\s+\d{2}:\d{2}\s+-\s+\+[\d\s]+:', line) and '|' in line:
                company_name = self.extract_company_name(line)
                
                # Skip if company name is too short or empty
                if not company_name or len(company_name) < 2:
                    i += 1
                    continue
                
                company_count += 1
                print(f"\n{'='*60}")
                print(f"COMPANY #{company_count}: {company_name}")
                print(f"{'='*60}")
                
                # Initialize temp dict
                temp_dict = {key: "" for key in self.company_dict.keys()}
                temp_dict["name"] = company_name
                
                # Process subsequent lines
                i += 1
                current_key = None
                current_value = []
                
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Check if we've reached next company (next message with date/phone)
                    if re.match(r'^\d{2}/\d{2}/\d{2},\s+\d{2}:\d{2}\s+-\s+\+[\d\s]+:', line):
                        break
                    
                    if not line:
                        i += 1
                        continue
                    
                    # Check if this line is a key (format: *Key:* value or *Key:*)
                    matched_key = self.normalize_key(line)
                    
                    if matched_key:
                        # Save previous key-value
                        if current_key:
                            value = " | ".join([v for v in current_value if v])
                            temp_dict[current_key] = value
                            print(f"  {current_key}: {value}")
                        
                        # Start new key-value
                        current_key = matched_key
                        # Extract value after the colon (remove asterisks)
                        value_part = line.strip('*').split(":", 1)[1].strip() if ":" in line else ""
                        current_value = [value_part] if value_part else []
                    elif current_key:
                        # Continuation of current key
                        # Remove leading asterisks, bullets, and special chars
                        clean_line = line.lstrip('*').lstrip('•').lstrip('-').lstrip('\u2060').strip()
                        # Skip lines that are clearly notes or other sections we don't want
                        if clean_line and not clean_line.startswith("_"):
                            current_value.append(clean_line)
                    
                    i += 1
                
                # Save last key-value
                if current_key:
                    value = " | ".join([v for v in current_value if v])
                    temp_dict[current_key] = value
                    print(f"  {current_key}: {value}")
                
                # Add to main dict
                for key in self.company_dict.keys():
                    self.company_dict[key].append(temp_dict[key])
                
                continue
            
            i += 1
        
        print(f"\n{'='*60}")
        print(f"TOTAL COMPANIES FOUND: {company_count}")
        print(f"{'='*60}\n")
        
        # Length handling
        handler = lenhandling()
        self.company_dict = handler.lenhandling(self.company_dict)

        try:
            df = pd.DataFrame.from_dict(self.company_dict)
            print("\nDataFrame Preview:")
            print(df.to_string())
            
            newfilename = input("\nEnter the filename to save the excel (without .xlsx extension): ")
            newfilename_path = os.path.join(os.getcwd(), newfilename + ".xlsx")
            print(f"Saving to: {newfilename_path}")
            
            excel_cleaner = excelcleaner()
            excel_cleaner.filecleaner(df, newfilename_path)
        except Exception as e:
            print("Error writing Excel:", e)
            raise
        finally:
            print("Dictionary update completed.")

if __name__ == "__main__":
    try:
        file_reader = FileReader()
        chat_text=input("Enter chat text file path: ")
        file_reader.dictupdate(chat_text)
    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()
    finally:
        print("Execution completed.")