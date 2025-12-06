import pandas as pd
from arrlenhandling import lenhandling
import os
import re

class excelcleaner:
    @staticmethod
    def filecleaner(dataframe, newfilename: str):
        df = dataframe
        df = df.dropna(how='all')
        df.to_excel(newfilename, index=False, engine='openpyxl')
        return df
    def filecleaner_advanced(dataframe):
            
            #file_path=os.path.join(os.getcwd(),file_name)
            filename=filename
            df=pd.read_csv(rf'{filename}',encoding='utf-8')
            df=df.drop(columns=["Application Link"])
            print(df.head())
            
            rowlist = df.index.tolist()
            #print(df.at[232,"Job Role"])
            for row in rowlist:
                if pd.isna(df.at[row, "Job Role"]) and pd.isna(df.at[row, "CTC"]):
                    df = df.drop(row)
                    print("dropped row:", row)
            return df

        
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

    def process_content(self, content: str, verbose=False):
        """Process file content (string) and return DataFrame - for Streamlit"""
        lines = content.split('\n')
        
        # Reset company_dict for new processing
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
        
        i = 0
        company_count = 0
        processing_log = []
        
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
                if verbose:
                    processing_log.append(f"COMPANY #{company_count}: {company_name}")
                
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
                            if verbose:
                                processing_log.append(f"  {current_key}: {value}")
                        
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
                    if verbose:
                        processing_log.append(f"  {current_key}: {value}")
                
                # Add to main dict
                for key in self.company_dict.keys():
                    self.company_dict[key].append(temp_dict[key])
                
                continue
            
            i += 1
        
        if verbose:
            processing_log.append(f"TOTAL COMPANIES FOUND: {company_count}")
        
        # Length handling
        handler = lenhandling()
        self.company_dict = handler.lenhandling(self.company_dict)

        # Create DataFrame
        df = pd.DataFrame.from_dict(self.company_dict)
        
        return df, processing_log if verbose else df

    def dictupdate(self, filename: str):
        """Original method for CLI usage"""
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
        new_df=excel_cleaner.filecleaner(df, newfilename_path)
        excel_cleaner.filecleaner_advanced(new_df)
        
        print("Dictionary update completed.")
        return df

if __name__ == "__main__":
    try:
        file_reader = FileReader()
        chat_text = r"D:\chatexport\tester.txt"
        file_reader.dictupdate(chat_text)
        try:
            show=file_reader.process_content(chat_text)
            print(show)
        except exception as e:
            print("exception happened in the lines between the 230 to 237")
    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()
    finally:
        print("Execution completed.")