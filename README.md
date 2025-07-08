# SDTMAI - A CDISC Genius Product

SDTMAI is a professional web application that provides AI-powered access to SDTM (Study Data Tabulation Model) variable details via the CDISC Library API. This tool helps clinical data professionals retrieve complete variable information without the need to manually search through documentation.

## Features

- **AI-Powered Variable Search**: Query SDTM variables using natural language
- **Direct Variable Input**: Search specific SDTM variables via the sidebar
- **Dynamic Version Selection**: Choose from available SDTMIG and CT versions
- **Variable Details**: View comprehensive information about SDTM variables
- **Codelist Display**: Access and explore associated codelists
- **SDTMIG Downloads**: Download SDTMIG specification files directly from the app

## System Requirements

- Python 3.8+
- Internet connection (for API access)
- CDISC Library API key
- OpenAI API key

## Required Files

To run this application locally, you need:

1. **Python Files**:
   - `main.py` - Main application logic and Streamlit interface
   - `api_client.py` - CDISC Library API client
   - `utils.py` - Utility functions for formatting data
   - `ai_processor.py` - OpenAI integration for natural language processing

2. **SDTMIG Specification Files** (place in a folder named `attached_assets`):
   - `SDTMIG_3.4.xls`
   - `SDTMIG_3.3.xls`
   - `SDTMIG_3.2.xls`
   - `SDTMIG_3.1.3.xls`
   - `SDTMIG_3.1.2.xls`

3. **Configuration Files**:
   - `.streamlit/config.toml` - Streamlit configuration
   - `requirements.txt` - Python dependencies
   - `.env` - Environment variables for API keys (not tracked in version control)

## Installation Instructions

1. Clone this repository or download the files to your local VS Code environment.

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.streamlit` folder with a `config.toml` file containing:
   ```toml
   [server]
   headless = true
   address = "0.0.0.0"
   port = 5000
   ```

6. Create a `.env` file with your API keys:
   ```
   CDISC_API_KEY=your_cdisc_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

7. Run the application:
   ```bash
   streamlit run main.py
   ```

## Usage

1. **Search via Sidebar**:
   - Enter a SDTM variable name (e.g., AESER, LBCAT, VSTEST)
   - Click "Search Variable"

2. **Search via AI Chat**:
   - Type a natural language query (e.g., "Tell me about AESER")
   - Or use the conversation starter buttons

3. **View Results**:
   - Variable information displays in a tabbed interface
   - Associated codelists appear in a separate tab

4. **Download Specifications**:
   - Select your desired SDTMIG version
   - Click the download button in the sidebar

## Environment Setup

For the application to function properly, you need valid API credentials:

1. **CDISC Library API Key**: 
   - Register at [CDISC Library](https://www.cdisc.org/cdisc-library)
   - Once approved, obtain your API key

2. **OpenAI API Key**:
   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Generate an API key in your account settings

Add both keys to your `.env` file as shown in the installation section.

## Troubleshooting

- **API Connection Issues**: Ensure your API keys are valid and correctly set in the `.env` file
- **Missing Variables**: Verify you're using the correct SDTMIG version for the variable you're searching
- **Application Not Loading**: Check that all required packages are installed and the correct Python version is used

## License

This project is proprietary software created for CDISC data professionals.

---

© 2025 CDISC Genius. All rights reserved.