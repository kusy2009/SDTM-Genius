from typing import Dict, List, Optional
import pandas as pd

def format_variable_info(var_info: Dict) -> pd.DataFrame:
    """Format variable information into a pandas DataFrame"""
    formatted_data = []

    # Extract basic information
    for key, value in var_info.items():
        if key != "_links" and isinstance(value, (str, bool, int, float)):
            formatted_data.append({
                "Parameter": key,
                "Value": str(value)
            })

    return pd.DataFrame(formatted_data)

def format_codelist_info(codelist_data: Dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Format codelist information into two DataFrames - info and terms"""
    info_data = []
    terms_data = []

    if codelist_data:
        # Format basic information
        codelist_info = codelist_data.get("info", {})
        if isinstance(codelist_info, dict):
            for key, value in codelist_info.items():
                if key not in ["terms", "_links"]:
                    info_data.append({
                        "Parameter": key,
                        "Value": str(value)
                    })

        # Format terms like SAS macro output
        terms = codelist_data.get("terms", [])
        if terms:
            # Create DataFrame with specific columns matching SAS macro output
            terms_data = [{
                "Submission Value": term.get("submissionValue", ""),
                "Decoded Value": term.get("preferredTerm", "")
            } for term in terms]

    return pd.DataFrame(info_data), pd.DataFrame(terms_data)

def extract_codelist_ids(var_info: Dict) -> List[str]:
    """Extract codelist IDs following exact SAS macro logic"""
    codelist_ids = []

    # Follow SAS macro logic from lines 154-162
    if "_links" in var_info:
        links = var_info.get("_links", {})
        # Check if codelist is a list (matching SAS macro behavior)
        codelist = links.get("codelist", [])
        if isinstance(codelist, list):
            for item in codelist:
                if isinstance(item, dict):
                    href = item.get("href", "")
                    if href:
                        # Extract the last element from href (equivalent to scan(value, -1))
                        codelist_id = href.split("/")[-1]
                        if codelist_id:
                            codelist_ids.append(codelist_id)
        # Also check for single codelist entry
        elif isinstance(codelist, dict):
            href = codelist.get("href", "")
            if href:
                codelist_id = href.split("/")[-1]
                if codelist_id:
                    codelist_ids.append(codelist_id)

    return codelist_ids