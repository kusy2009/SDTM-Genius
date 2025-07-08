import streamlit as st
import pandas as pd
from api_client import CDISCLibraryAPI
from utils import format_variable_info, format_codelist_info, extract_codelist_ids
from ai_processor import AIQueryProcessor

# Page configuration
st.set_page_config(
    page_title="SDTMAI",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'selected_variable' not in st.session_state:
    st.session_state.selected_variable = ""

# Initialize API clients
@st.cache_resource
def get_api_client():
    return CDISCLibraryAPI()

@st.cache_resource
def get_ai_processor():
    return AIQueryProcessor()

api_client = get_api_client()
ai_processor = get_ai_processor()

# Add custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .st-emotion-cache-1y4p8pa {
        padding: 2rem;
    }
    .chat-input {
        border-radius: 20px;
        padding: 1rem;
        margin: 2rem 0;
    }
    .chat-result {
        background-color: #f8f9fa;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .conversation-starter {
        margin: 0.5rem;
        padding: 0.75rem 1.5rem;
        border-radius: 20px;
        background-color: #f0f2f6;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .conversation-starter:hover {
        background-color: #e0e2e6;
    }
    .chat-container {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.title("SDTMAI")
st.subheader("A CDISC Genius Product")

# Main chat interface
main_container = st.container()

with main_container:
    # Chat input area
    st.markdown("### Ask me about any SDTM variable")

    # Conversation starters as buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Tell me about EGTESTCD", key="starter1"):
            st.session_state.query = "Tell me about EGTESTCD"
    with col2:
        if st.button("🔍 What is AESER?", key="starter2"):
            st.session_state.query = "What is AESER?"

    col3, col4 = st.columns(2)
    with col3:
        if st.button("📋 Show LBCAT details", key="starter3"):
            st.session_state.query = "Show LBCAT details"
    with col4:
        if st.button("💉 Explain VSTEST", key="starter4"):
            st.session_state.query = "Explain VSTEST"

    # Chat input
    query = st.text_input(
        "",
        placeholder="Type your question here...",
        key="query"
    )

    # Process query
    if query:
        with st.spinner("Processing query..."):
            # Extract variable name from query
            extracted_var = ai_processor.extract_variable_name(query)
            if extracted_var:
                st.session_state.selected_variable = extracted_var

# Sidebar for inputs
with st.sidebar:
    st.header("Input Parameters")

    # Variable input with sync to session state
    var_input = st.text_input(
        "SDTM Variable Name",
        help="Enter an SDTM variable name (e.g., AESER, LBCAT, VSTEST)",
        key="manual_input"
    )
    
    # Add a submit button for variable input
    if st.button("Search Variable"):
        if var_input.strip():
            st.session_state.selected_variable = var_input.strip().upper()
    
    # Version selection
    st.subheader("Version Selection")

    # Get available versions
    sdtmig_versions = ["3-4"]  # Default version
    ct_versions = ["2024-09-27"]  # Default version

    try:
        # Fetch available versions
        sdtmig_versions = api_client.get_sdtmig_versions()
        ct_versions = api_client.get_ct_versions()

        if not sdtmig_versions:
            st.warning("Could not fetch SDTMIG versions. Using defaults.")
            sdtmig_versions = ["3-4", "3-3", "3-2"]

        if not ct_versions:
            st.warning("Could not fetch CT versions. Using defaults.")
            ct_versions = ["2024-09-27", "2024-03-29"]
    except Exception as e:
        st.error(f"Error fetching versions: {str(e)}")

    # Version dropdowns
    sdtmig_version = st.selectbox(
        "SDTMIG Version",
        options=sdtmig_versions,
        index=0,
        help="Select SDTMIG version (e.g., 3-4, 3-3)"
    )

    ct_version = st.selectbox(
        "CT Version",
        options=ct_versions,
        index=0,
        help="Select Controlled Terminology version (YYYY-MM-DD)"
    )

    st.info(f"Using SDTMIG v{sdtmig_version} and CT v{ct_version}")

    # SDTMIG Specification Download Section
    st.subheader("Download SDTMIG Specification")

    # Map versions to file paths
    version_to_file = {
        "3-4": "attached_assets/SDTMIG_3.4.xls",
        "3-3": "attached_assets/SDTMIG_3.3.xls",
        "3-2": "attached_assets/SDTMIG_3.2.xls",
        "3-1-3": "attached_assets/SDTMIG_3.1.3.xls",
        "3-1-2": "attached_assets/SDTMIG_3.1.2.xls"
    }
    
    # Also handle variant format if needed
    variant_formats = {
        "3.4": "3-4",
        "3.3": "3-3",
        "3.2": "3-2",
        "3.1.3": "3-1-3",
        "3.1.2": "3-1-2"
    }
    
    # Get proper version format for file lookup
    file_version = sdtmig_version
    if sdtmig_version in variant_formats.keys():
        file_version = variant_formats[sdtmig_version]
    
    # Add download button for the selected version in a styled container
    st.markdown("""
    <style>
    .download-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-top: 10px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="download-container">', unsafe_allow_html=True)
        st.markdown(f"#### SDTMIG v{sdtmig_version} Specification")
        
        if file_version in version_to_file:
            try:
                with open(version_to_file[file_version], "rb") as file:
                    st.download_button(
                        label=f"📥 Download Specification",
                        data=file,
                        file_name=f"SDTMIG_{sdtmig_version}.xls",
                        mime="application/vnd.ms-excel",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Error loading specification file: {str(e)}")
        else:
            st.warning(f"Specification file for SDTMIG v{sdtmig_version} not available")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Results preview container - displayed in a card-like interface
if st.session_state.selected_variable:
    st.markdown("---")
    
    # Add custom CSS for the card-like interface
    st.markdown("""
    <style>
    .result-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .result-header {
        background-color: #f0f7ff;
        padding: 15px;
        border-radius: 8px 8px 0 0;
        margin-bottom: 15px;
        border-bottom: 1px solid #e0e0e0;
    }
    .section-divider {
        margin: 15px 0;
        border-top: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main result container
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    
    # Header section
    st.markdown('<div class="result-header">', unsafe_allow_html=True)
    st.markdown(f"### Variable: {st.session_state.selected_variable}")
    st.markdown(f"*Using SDTMIG v{sdtmig_version} and CT v{ct_version}*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    try:
        # Get variable information
        with st.spinner("Retrieving variable information..."):
            var_info, dataset = api_client.get_variable_info(st.session_state.selected_variable, sdtmig_version)

        if var_info and dataset:
            # Create tabs for better organization
            info_tab, codelist_tab = st.tabs(["Variable Information", "Associated Codelists"])
            
            with info_tab:
                st.markdown(f"#### {dataset}.{st.session_state.selected_variable}")
                
                if "description" in var_info:
                    st.info(var_info["description"])
                
                # Display key information at the top
                key_info = {}
                for key in ["label", "role", "core", "simpleDatatype"]:
                    if key in var_info:
                        key_info[key] = var_info[key]
                
                if key_info:
                    key_cols = st.columns(len(key_info))
                    for i, (k, v) in enumerate(key_info.items()):
                        with key_cols[i]:
                            st.metric(k.capitalize(), v)
                
                # Full variable information in an expandable section
                with st.expander("View all variable details", expanded=False):
                    var_df = format_variable_info(var_info)
                    st.dataframe(var_df, use_container_width=True)
            
            with codelist_tab:
                # Codelist information
                codelist_ids = extract_codelist_ids(var_info)
                if codelist_ids:
                    if len(codelist_ids) > 1:
                        cl_tabs = st.tabs([f"Codelist {i+1}" for i in range(len(codelist_ids))])
                        
                        for tab, codelist_id in zip(cl_tabs, codelist_ids):
                            with tab:
                                with st.spinner(f"Loading codelist {codelist_id}..."):
                                    codelist_data = api_client.get_codelist(codelist_id, ct_version)
                                    if codelist_data:
                                        info_df, terms_df = format_codelist_info(codelist_data)
                                        
                                        st.markdown("##### Codelist Information")
                                        st.dataframe(info_df, use_container_width=True)
                                        
                                        st.markdown("##### Codelist Terms")
                                        st.dataframe(terms_df, use_container_width=True)
                    else:
                        # Single codelist display
                        codelist_id = codelist_ids[0]
                        with st.spinner(f"Loading codelist {codelist_id}..."):
                            codelist_data = api_client.get_codelist(codelist_id, ct_version)
                            if codelist_data:
                                info_df, terms_df = format_codelist_info(codelist_data)
                                
                                st.markdown("#### Codelist Information")
                                st.dataframe(info_df, use_container_width=True)
                                
                                st.markdown("#### Codelist Terms")
                                st.dataframe(terms_df, use_container_width=True)
                else:
                    st.info("No codelists associated with this variable")
        else:
            st.error(f"Variable {st.session_state.selected_variable} not found in SDTMIG v{sdtmig_version}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("Powered by CDISC Library API")