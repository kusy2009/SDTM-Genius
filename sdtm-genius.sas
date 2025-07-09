/**
@file sdtmgenius.sas
@brief Automatically fetches SDTMIG version and retrieves SDTM metadata
@details
This macro is designed to automatically fetch the latest SDTMIG version from the CDISC Library if not explicitly provided by the user. It retrieves SDTM metadata, including dataset and variable details, and identifies the dataset to which a specified SDTM variable belongs. Additionally, it fetches codelist values for the variable if available.

Example usage:
@code
%sdtmgenius(sdtmvar=AEDECOD, sdtmigversion=3.2, sdtmctversion=2021-06-25);
@endcode

@param sdtmvar The SDTM variable name (e.g., AEDECOD)
@param sdtmigversion The SDTMIG version (optional)
@param sdtmctversion The SDTM Controlled Terminology version (optional)

@return Details of the specified SDTM variable, including codelist values if available
@version 1.0
@author Sai

<h4>SAS Macros</h4>
@li GetCDISCCodelist

@warning Ensure that the CDISC API key is correctly set in the macro variable &cdiscapikey
@note The macro automatically fetches the latest SDTMIG version if not provided by the user

@todo Add functionality to handle additional SDTM standards

@maintenance 
- 2025-01-21: Initial implementation Sai
*/

%macro sdtmgenius(sdtmvar=, sdtmigversion=, sdtmctversion=);

	/*----------------------------------------------------------------------------------------------------------/
	    If user does not explicitly provide an SDTMIG version, fetch the latest from the CDISC Library
	/----------------------------------------------------------------------------------------------------------*/
	%if %superq(sdtmigversion)= %then %do;
	
	    /*----------------------------------------------------------------------------------------------------------/
	        1) Retrieve all SDTMIG products from the Library
	    /----------------------------------------------------------------------------------------------------------*/
	    filename main TEMP;
	    proc http
	        url="https://library.cdisc.org/api/mdr/products"
	        method="GET"
	        out=main;
	        headers
	            "api-key"="&cdiscapikey" 
	            "Accept"="application/json"; 
	    run;
	
	    libname main json fileref=main;
	
	    /*----------------------------------------------------------------------------------------------------------/
	        2) Filter only the 'Human Clinical' SDTMIG entries and parse out the version from the href
	    /----------------------------------------------------------------------------------------------------------*/
	    data filtered_data;
	        set main._links_sdtmig;
	        if index(upcase(title), 'HUMAN CLINICAL') > 0;
	        sdtmigversion = scan(href, 3, '/'); 
	    run;
	
	    proc sort data=filtered_data;
	        by descending sdtmigversion;
	    run;
	
	    /*----------------------------------------------------------------------------------------------------------/
	        3) Keep only the highest (latest) version
	    /----------------------------------------------------------------------------------------------------------*/
	    data latest_version;
	        set filtered_data;
	        if _N_ = 1; 
	    run;
	
	    /*----------------------------------------------------------------------------------------------------------/
	        4) Assign macro variable &sdtmigversion to this latest version
	    /----------------------------------------------------------------------------------------------------------*/
	    proc sql noprint;
	        select sdtmigversion into :sdtmigversion trimmed
	        from latest_version;
	    quit;
	
	    %put NOTE: (sdtmgenius) Automatically fetched SDTMIG version = &sdtmigversion;
	
	%end;

    /*----------------------------------------------------------------------------------------------------------/
        Temporary file reference for the SDTM JSON metadata
    /----------------------------------------------------------------------------------------------------------*/
    filename sdtm TEMP;
  
    proc http
        url="https://library.cdisc.org/api/mdr/sdtmig/&sdtmigversion"
        method="GET"
        out=sdtm;
        headers
            "api-key"="&cdiscapikey" 
            "Accept"="application/json"; 
    run;

    libname sdtm json fileref=sdtm;

    /*----------------------------------------------------------------------------------------------------------/
        Dataset Sheet
    /----------------------------------------------------------------------------------------------------------*/
    data dataset_sheet;
        retain Dataset Description Class Structure Purpose;
        merge sdtm.CLASSES(in=a keep=ordinal_classes label) 
              sdtm.CLASSES_DATASETS(in=b drop=description ordinal rename=(name=Dataset label=Description datasetStructure=Structure));
        by ordinal_classes;
        if a and b;
        Purpose="Tabulation";
        Class=upcase(strip(label));
    run;

    /*----------------------------------------------------------------------------------------------------------/
        Variable Sheet
    /----------------------------------------------------------------------------------------------------------*/
    data Variable_sheet;
        merge dataset_sheet(in=a keep=ordinal_datasets Dataset) 
              sdtm.DATASETS_DATASETVARIABLES(in=b drop=description rename=(name=Variable simpleDatatype=DataType describedValueDomain=Codelist));
        by ordinal_datasets;
        if a and b;
        if core='Req' then Mandatory='Yes'; else Mandatory='No';
        order=input(ordinal,best.);
    run;

    /*----------------------------------------------------------------------------------------------------------/
        Identify which dataset the &sdtmvar belongs to
    /----------------------------------------------------------------------------------------------------------*/
    proc sql noprint;
        select strip(compbl(dataset)) into: dataset trimmed 
        from Variable_sheet
        where variable="&sdtmvar";
    quit;

    %PUT NOTE: Dataset resolved to &dataset;

    /*----------------------------------------------------------------------------------------------------------/
        If we cannot find the dataset, abort the macro
    /----------------------------------------------------------------------------------------------------------*/
    %if %length(&dataset)=0 %then %do;
        %put NOTE: Aborting macro since dataset is missing. Please check input variable &sdtmvar and update;
        %return;
    %end; 
    %else %do;

        /*----------------------------------------------------------------------------------------------------------/
            Get details of the variable from the API
        /----------------------------------------------------------------------------------------------------------*/
        filename varcheck TEMP;
        proc http
            url="https://library.cdisc.org/api/mdr/sdtmig/&sdtmigversion/datasets/&dataset/variables/&sdtmvar"
            method="GET"
            out=varcheck;
            headers
                "api-key"="&cdiscapikey"
                "Accept"="application/json";
        run;

        libname varcheck JSON fileref=varcheck;
        
        data varinfo;
            set varcheck.alldata;
            keep p1 value;
            if p2='parentDataset' and p3='title' then p1='DatasetLabel';
            if p1 ne '_links';
        run;

        /*----------------------------------------------------------------------------------------------------------/
            Print variable info
        /----------------------------------------------------------------------------------------------------------*/
        title "Details of CDISC SDTM variable &dataset.&sdtmvar (SDTM IG Version=&sdtmigversion)";
        proc print data=varinfo noobs label;
            var p1 value;
            label p1 = "Parameter" 
                  value="Value";
        run;
        title;

        /*----------------------------------------------------------------------------------------------------------/
            Extract Codelist Values (could be multiple)
        /----------------------------------------------------------------------------------------------------------*/
        %let codelistValue=;

        proc sql noprint;
            select distinct strip(scan(value, -1))
            into :codelistValue separated by ' '
            from varcheck.alldata
            where index(upcase(p2), "CODELIST") > 0 
              and p3 = "href";
        quit;
        
        %put NOTE: Extracted CODELIST = &codelistValue;

        /*----------------------------------------------------------------------------------------------------------/
            If no codelist is present, exit 
        /----------------------------------------------------------------------------------------------------------*/
        %if %length(&codelistValue)=0 %then %do;
            %put NOTE: CODELIST is not present for this variable;
            %return;
        %end;

        /*----------------------------------------------------------------------------------------------------------/
            If at least one codelist is present, call %GetCDISCCodelist for each
        /----------------------------------------------------------------------------------------------------------*/
        %else %if %length(&codelistValue)>0 %then %do;
            
            /*--------------------------------------------------------------------------------*/
            /*    Macro to retrieve the CDISC CT for a given single codelistValue             */
            /*    (slightly updated to accept codelistValue as a parameter)                   */
            /*--------------------------------------------------------------------------------*/
            %macro GetCDISCCodelist(
                codelistValue=,
                codelistType=CodelistCode,  /* Match by ID or CodelistCode */
                standard=SDTM,              /* Default to SDTM */
                outlib=WORK                /* Output Library */
            );
            
                /*----------------------------------------------------------------------------------------------------------/
                    Validate input
                /----------------------------------------------------------------------------------------------------------*/
                %if %superq(codelistValue)= %then %do;
                    %put ERROR: You must specify a codelistValue= (e.g., C120523 for EGTESTCD etc);
                    %return;
                %end;
            
                /*----------------------------------------------------------------------------------------------------------/
                    Ensure correct standard input
                /----------------------------------------------------------------------------------------------------------*/
                %let valid_standards = SDTM ADAM CDASH DEFINE-XML SEND DDF GLOSSARY MRCT PROTOCOL QRS QS-FT TMF;
                %if not (%sysfunc(indexw(&valid_standards, %upcase(&standard)))) %then %do;
                    %put ERROR: Invalid standard "&standard". Supported values are:;
                    %put ERROR: &valid_standards;
                    %return;
                %end;
            
                /*----------------------------------------------------------------------------------------------------------/
                    Convert standard to API format
                /----------------------------------------------------------------------------------------------------------*/
                %let api_standard = %lowcase(&standard)ct;
            
                /*----------------------------------------------------------------------------------------------------------/
                    Dynamically fetch available versions if not provided
                /----------------------------------------------------------------------------------------------------------*/
                %if %superq(sdtmctversion)= %then %do;
                    %put NOTE: Version is not specified. Fetching the latest version...;
            
                    filename version TEMP;
                    proc http
                        url="https://api.library.cdisc.org/api/mdr/products/Terminology"
                        method="GET"
                        out=version;
                        headers
                            "api-key"="&cdiscapikey"
                            "Accept"="application/json";
                    run;
            
                    libname version JSON fileref=version;
                    
                    data versions;
                        set version._LINKS_PACKAGES;
                        /* Extract the standard from href, remove '/package.json' at the end */
                        standard_from_href = scan(href, 4, '/'); 
                        standard_from_href = substr(standard_from_href, 1, length(standard_from_href)-13);
                        if upcase(standard_from_href)=upcase("&standard");
                        
                        /* Extract the date (YYYY-MM-DD) from the href field */           
                        version_date = substr(href, length(href)-9, 10);
                        keep version_date standard_from_href;
                    run;
                    
                    proc sort data=versions;
                        by descending version_date;
                    run;
                    
                    data _null_;
                        set versions(obs=1);
                        call symputx('sdtmctversion', version_date);
                    run;
            
                    %put NOTE: Latest &standard CT version is &sdtmctversion;
                %end;
            
                /*----------------------------------------------------------------------------------------------------------/
                    Fetch the specific standard CT package
                /----------------------------------------------------------------------------------------------------------*/
                filename cdiscCT TEMP;
                proc http
                    url="https://api.library.cdisc.org/api/mdr/ct/packages/&api_standard.-&sdtmctversion."
                    method="GET"
                    out=cdiscCT;
                    headers
                        "api-key"="&cdiscapikey"
                        "Accept"="application/json";
                run;
            
                libname cdisc JSON fileref=cdiscCT;
            
                /*----------------------------------------------------------------------------------------------------------/
                    Extract Codelist-level data
                /----------------------------------------------------------------------------------------------------------*/
                data _codelist_data;
                    retain submissionValue conceptId name extensible ordinal_codelists;
                    set cdisc.CODELISTS(keep=conceptId submissionValue extensible name ordinal_codelists);
                    rename 
                        conceptId       = CodelistCode
                        submissionValue = ID;
                run;
            
                /*----------------------------------------------------------------------------------------------------------/
                    Extract Term-level data
                /----------------------------------------------------------------------------------------------------------*/
                data _codelist_terms_data;
                    retain submissionValue conceptId preferredTerm ordinal_codelists;
                    set cdisc.CODELISTS_TERMS(keep=ordinal_codelists conceptId submissionValue preferredTerm);
                    rename 
                        submissionValue = TERM
                        conceptId       = TermCode
                        preferredTerm   = DecodedValue;
                run;
            
                /*----------------------------------------------------------------------------------------------------------/
                    Merge codelist and terms
                /----------------------------------------------------------------------------------------------------------*/
                proc sql;
                    create table &outlib..merged_codelists as
                    select 
                        a.*,
                        b.TermCode,
                        b.TERM,
                        b.DecodedValue as TermDecodedValue
                    from _codelist_data as a
                    inner join _codelist_terms_data as b
                    on a.ordinal_codelists = b.ordinal_codelists
                    order by a.ID, b.TERM;
                quit;
            
                proc format;
                    value $extensible_fmt
                        "true"  = "Yes"
                        "false" = "No";
                run;
            
                /*----------------------------------------------------------------------------------------------------------/
                    Filter for the specific codelist
                /----------------------------------------------------------------------------------------------------------*/
                data &outlib..specific_codelist;
                    set &outlib..merged_codelists;
                    length ExtensibleYN $3;
                    ExtensibleYN = put(Extensible, $extensible_fmt.);
                
                    %if %upcase(&codelistType)=ID %then %do;
                        where upcase(ID) = upcase("&codelistValue");
                    %end;
                    %else %if %upcase(&codelistType)=CODELISTCODE %then %do;
                        where upcase(CodelistCode) = upcase("&codelistValue");
                    %end;
                run;
            
                /*----------------------------------------------------------------------------------------------------------/
                    Check if codelist exists
                /----------------------------------------------------------------------------------------------------------*/
                proc sql noprint;
                    select count(*) into: check_exists
                    from &outlib..specific_codelist;
                    select distinct ExtensibleYN into: Extensible
                    from &outlib..specific_codelist;
                quit;
            
                /*----------------------------------------------------------------------------------------------------------/
                    If not found, print warning and exit
                /----------------------------------------------------------------------------------------------------------*/
                %if &check_exists = 0 %then %do;
                    %put WARNING: The provided Codelist Value "&codelistValue" does not exist in the &standard Controlled Terminology version &sdtmctversion.;
                    %put WARNING: Please check if your ID is correct or if it exists in the &standard Codelists.;
                    title "Codelist Value Not Found";
                    data _null_;
                        file print;
                        put "------------------------------------------------------------";
                        put "WARNING: The specified Codelist Value '&codelistValue' was not found in &standard CT Version &sdtmctversion.";
                        put "Please verify your input value.";
                        put "------------------------------------------------------------";
                    run;
                    title;
                    %return;
                %end;
            
                /*----------------------------------------------------------------------------------------------------------/
                    Output results
                /----------------------------------------------------------------------------------------------------------*/
                title "Submission Values for &codelistType=&codelistValue (&standard. CT Version=&sdtmctversion, Extensible=&Extensible)";
                proc print data=&outlib..specific_codelist noobs label;
                    var TERM termdecodedvalue;
                    label TERM = "Submission Value" 
                          termdecodedvalue="Decoded Value";
                run;
                title;
            
            %mend GetCDISCCodelist;

            /*----------------------------------------------------------------------------------------------------------/
               We now split &codelistValue by spaces and call %GetCDISCCodelist 
               once for each separate value
            /----------------------------------------------------------------------------------------------------------*/
            %local i singleCode;
            %let i=1;
            %do %while(%scan(&codelistValue,&i,%str( )) ne %str());
                %let singleCode=%scan(&codelistValue,&i,%str( ));
                /* Call macro for each codelist value */
                %GetCDISCCodelist(codelistValue=&singleCode);
                %let i=%eval(&i+1);
            %end;

        %end; /* end of multiple codelist logic */
    %end; /* end of else for dataset existence */

%mend sdtmgenius;
