class lenhandling:
    def lenhandling(self,company_dict):
        for key in company_dict:
            max_len = max(len(v) for v in company_dict.values())
            if len(company_dict[key]) < max_len:
                company_dict[key] += ['N/A'] * (max_len - len(company_dict[key]))
        return company_dict
        """ this is the code written for handling the unequal lengths of arrays in a dictionary which are eventually converted to a"" dataframe   
        """"nan or avrage or mean"""
        