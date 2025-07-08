import requests
import os
from typing import Dict, List, Optional, Tuple, Union
import json

class CDISCLibraryAPI:
    def __init__(self):
        self.api_key = os.getenv("CDISC_API_KEY")
        self.base_url = "https://library.cdisc.org/api/mdr"
        self.headers = {
            "api-key": self.api_key,
            "Accept": "application/json"
        }

    def get_sdtmig_versions(self) -> List[str]:
        """Get SDTMIG versions following SAS macro logic"""
        try:
            # 1) Retrieve all SDTMIG products from the Library
            response = requests.get(
                f"{self.base_url}/products",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            # 2) Filter only the 'Human Clinical' SDTMIG entries
            filtered_versions = []
            for item in data.get("_links", {}).get("sdtmig", []):
                if "HUMAN CLINICAL" in item.get("title", "").upper():
                    version = item["href"].split("/")[2]  # Same as scan(href, 3, '/')
                    filtered_versions.append(version)

            # 3) Sort versions descending
            versions = sorted(filtered_versions, reverse=True)
            if not versions:
                versions = ["3-4", "3-3", "3-2"]  # Default versions if none found

            print(f"Found SDTMIG versions: {versions}")
            return versions

        except Exception as e:
            print(f"Error fetching SDTMIG versions: {str(e)}")
            return ["3-4", "3-3", "3-2"]

    def get_latest_sdtmig_version(self) -> str:
        """Get latest SDTMIG version"""
        versions = self.get_sdtmig_versions()
        return versions[0]

    def get_ct_versions(self) -> List[str]:
        """Get CT versions following SAS macro logic"""
        try:
            response = requests.get(
                "https://api.library.cdisc.org/api/mdr/products/Terminology",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            # Extract version dates from packages
            ct_versions = []
            for item in data.get("_links", {}).get("packages", []):
                href = item.get("href", "")
                if "sdtmct" in href.lower():
                    # Extract the date (YYYY-MM-DD) from href
                    version_date = href[-23:-13]  # Extract YYYY-MM-DD format
                    if version_date and version_date.count("-") == 2:  # Validate date format
                        ct_versions.append(version_date)

            versions = sorted(ct_versions, reverse=True)
            if not versions:
                versions = ["2024-09-27", "2024-03-29", "2023-12-22"]

            print(f"Found CT versions: {versions}")
            return versions

        except Exception as e:
            print(f"Error fetching CT versions: {str(e)}")
            return ["2024-09-27", "2024-03-29", "2023-12-22"]

    def get_latest_ct_version(self) -> str:
        """Get latest CT version"""
        versions = self.get_ct_versions()
        return versions[0]

    def get_variable_info(self, sdtmvar: str, sdtmig_version: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get variable information and its dataset following SAS macro logic"""
        try:
            # First get all datasets and variables
            response = requests.get(
                f"{self.base_url}/sdtmig/{sdtmig_version}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            # Find the dataset containing our variable
            dataset = None
            for class_info in data.get("classes", []):
                for ds in class_info.get("datasets", []):
                    for var in ds.get("datasetVariables", []):
                        if var.get("name") == sdtmvar:
                            dataset = ds.get("name")
                            break
                    if dataset:
                        break
                if dataset:
                    break

            if not dataset:
                print(f"Dataset not found for variable {sdtmvar}")
                return None, None

            # Get detailed variable information (matching SAS macro's direct variable fetch)
            response = requests.get(
                f"{self.base_url}/sdtmig/{sdtmig_version}/datasets/{dataset}/variables/{sdtmvar}",
                headers=self.headers
            )
            response.raise_for_status()
            var_info = response.json()

            # Print the raw response for debugging
            print(f"Variable info response: {json.dumps(var_info, indent=2)}")

            return var_info, dataset

        except Exception as e:
            print(f"Error fetching variable info: {str(e)}")
            return None, None

    def get_codelist(self, codelist_id: str, ct_version: str) -> Optional[Dict]:
        """Get codelist information following SAS macro logic"""
        try:
            # Match the SAS macro's URL construction exactly
            response = requests.get(
                f"https://api.library.cdisc.org/api/mdr/ct/packages/sdtmct-{ct_version}/codelists/{codelist_id}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            # Format response to match SAS macro's output structure
            codelist_info = {
                "info": {
                    "name": data.get("name"),
                    "conceptId": data.get("conceptId"),
                    "submissionValue": data.get("submissionValue"),
                    "extensible": "Yes" if data.get("extensible") else "No",
                    "description": data.get("description")
                },
                "terms": []
            }

            # Add terms if they exist (matching SAS macro's terms handling)
            terms = data.get("terms", [])
            for term in terms:
                codelist_info["terms"].append({
                    "submissionValue": term.get("submissionValue"),
                    "preferredTerm": term.get("preferredTerm"),
                    "conceptId": term.get("conceptId")
                })

            return codelist_info

        except Exception as e:
            print(f"Error fetching codelist: {str(e)}")
            return None