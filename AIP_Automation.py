import os
import subprocess
import csv
import datetime
import threading
import logging
import re
import ast
from typing import List, Tuple

# Optional dependencies for Step 2
try:
    import pandas as pd
except Exception as _e:  # pragma: no cover
    pd = None
try:
    import psycopg2
    from psycopg2 import sql
except Exception as _e:  # pragma: no cover
    psycopg2 = None
    sql = None

# Optional dependencies for Step 3
try:
    from neo4j import GraphDatabase
except Exception as _e:  # pragma: no cover
    GraphDatabase = None

# Mapping dictionary for return codes and their corresponding messages
return_code_messages = {
    0: "No errors, processing was completed correctly. This is also the return code for --help and --version parameters.",
    1: "API key missing. No API key was provided either in the prompt or in the environment variable.",
    2: "Login Error. Unable to login to AIP Console with the given API key. Please check that you provide the proper value.",
    3: "Upload Error. An error occurred during upload to AIP Console. Check the standard output to see more details.",
    4: "Add Version Job Error. Creation of the Add Version job failed, or AIP CLI is unable to get the status of the running job. Please see the standard output for more details regarding this error.",
    5: "Job terminated. The Add Version job did not finish in an expected state. Check the standard output or AIP Console for more details about the state of the job.",
    6: "Application name or GUID missing. The AddVersion job cannot run due to a missing application name or missing application guid.",
    7: "Application Not Found. The given Application Name or GUID could not be found.",
    8: "Source Folder Not Found. The given source folder could not be found on the AIP Node where the application version is delivered.",
    9: "No Version. Application has no version and the provided command cannot be run.",
    10: "Version Not Found. The given version could not be found OR no version matches the requested command (i.e. No delivered version exists to be used for analysis)",
    1000: "Unexpected error. This can occur for various reasons, and the standard output should be checked for more information."
}

# Function to read properties from the config file
def read_properties_file(filename):
    properties = {}
    print(f"Reading properties from file: {filename} \n")
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('['):  # Skip empty lines and comments
                key, value = line.split('=', 1)
                properties[key.strip()] = value.strip()
    return properties

# Function to validate config properties
def validate_config(properties):
    required_params = ['console_url', 'console_api_key', 'console_cli_path', 'source_code_path', 'max_batches', 'applications_file', 'output_csv_file_path', 'output_txt_file_path', 'output_log_file_path']
    for param in required_params:
        if param not in properties:
            print(f"Program stopped because required parameter '{param}' is not in the config.properties \n")
            raise ValueError(f"Required parameter '{param}' is not in the config.properties")
        
def replace_special_characters_with_underscore(input_string):
    input_string = input_string.replace("^", "").replace("&", "").replace("'","").replace("@","").replace("{","").replace("}","").replace("[","").replace("]","").replace(",","").replace("$","").replace("=","").replace("!","").replace("-","").replace("#","").replace("(","").replace(")","").replace("%","").replace(".","").replace("+","").replace("~","").replace("_","")
    # Define a regular expression pattern to match spaces and special characters
    pattern = r'[^a-zA-Z0-9_\s]'

    # Use the sub() function from the re module to replace matches with underscores
    output_string = re.sub(pattern, '_', input_string)

    return output_string

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

# Function to process application
def process_application(app_batch, console_url, console_api_key, console_cli, source_code_path, logger, output_csv_file, output_txt_file):
    try:
        # print(f"Executing Batch: {app_batch} \n")
        # logger.info(f"Executing Batch: {app_batch}")
        for application_name, app_domain, source_code in app_batch:

            app_name = replace_special_characters_with_underscore(application_name)

            print(f"Application -> '{application_name}' is renamed as '{app_name}' \n")
            logger.info(f"Application -> '{application_name}' is renamed as '{app_name}' \n")

            print(f"Running AIP Analysis for the application -> '{app_name}' ..... \n")
            logger.info(f"Running AIP Analysis for the application -> '{app_name}' ..... \n")

            command = [
                'java', '-jar', f'"{console_cli}"',
                'Onboard-Application',
                '--app-name', f'"{app_name}"',
                '--domain-name', f'"{app_domain}"',
                '--file-path', f'"{source_code_path}\\{source_code}"',
                '--server-url',  f'{console_url}',
                '--apikey', f'{console_api_key}',
                '--verbose=true',
                '--process-imaging=true',
                '--exclude-patterns="tmp/, temp/, *test, tests, target/, .svn/, .git/, _Macosx/, test/"'
            ]
            # print(command)
            cmd = " ".join(command)
            # print(cmd)
            print(f"Executing command to run AIP Analysis for the Application -> '{app_name}' : {cmd} \n")
            logger.info(f"Executing command to run AIP Analysis for the Application -> '{app_name}' : {cmd} \n")
            # logger.info("Executing command:", " ".join(command))

            # completed_process = subprocess.run(command, capture_output=True, text=True)

            return_code, stdout, stderr = run_command(cmd)
            # print("Return Code:", return_code)
            # print("Standard Output:", stdout)
            # print("Standard Error:", stderr)

            if return_code == 0:
                status = "Passed"
                reason = "Application processed successfully"
                print(f"Application -> '{app_name}' processed successfully \n")
                logger.info(f"Application -> '{app_name}' processed successfully \n")

            elif return_code in return_code_messages.keys():
                status = "Failed"
                reason = return_code_messages.get(return_code, f"known return code: {return_code} - {return_code_messages[return_code]}")
                print(f"Application -> '{app_name}' Failed with known return code: {return_code} - {return_code_messages[return_code]} \n")
                logger.info(f"Application -> '{app_name}' Failed with known return code: {return_code} - {return_code_messages[return_code]} \n")   

            else:
                status = "Failed"
                reason = return_code_messages.get(return_code, f"Unknown return code: {return_code}")
                print(f"Application -> '{app_name}' Failed with Unknown return code: {return_code} \n")
                logger.info(f"Application -> '{app_name}' Failed with Unknown return code: {return_code} \n")               

            # Write output data to CSV
            with open(output_csv_file, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([app_name, status, reason])

            # Write output data to text file
            with open(output_txt_file, 'a', newline='') as txtfile:
                txtfile.write(f"{app_name}: {status} - {reason}\n")

    except Exception as e:
        print(f"Error processing application -> '{app_name}' : {e} \n")
        logger.error(f"Error processing application -> '{app_name}' : {e} \n")

# Function to create batches
def create_batches(applications, num_batches):
    batch_size = len(applications) // num_batches
    remaining_apps = len(applications) % num_batches
    batches = []
    start = 0
    
    for i in range(num_batches):
        batch_end = start + batch_size + (1 if i < remaining_apps else 0)
        batches.append(applications[start:batch_end])
        start = batch_end
    
    return batches

# Function to process batch
def process_batch(batches, console_url, console_api_key, console_cli, source_code_path, logger, output_csv_file, output_txt_file):
    process_threads = []
    for app_batch in batches:
        thread = threading.Thread(target=process_application, args=(app_batch, console_url, console_api_key, console_cli, source_code_path, logger, output_csv_file, output_txt_file))
        thread.start()
        process_threads.append(thread)
    for thread in process_threads:
        thread.join()

def step_1_run_aip_analysis():
    try:
        current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Read properties from the config file
        properties = read_properties_file('config.properties')

        # Validate config properties
        validate_config(properties)

        console_url = properties['console_url']
        console_api_key = properties['console_api_key']
        console_cli = properties['console_cli_path']
        source_code_path = properties['source_code_path']
        applications_file = properties['applications_file']
        max_batches = int(properties['max_batches'])

        output_csv_file = os.path.join(properties['output_csv_file_path'], f"AIP_Analysis_Results_{current_datetime}.csv")
        output_txt_file = os.path.join(properties['output_txt_file_path'], f"AIP_Analysis_Results_{current_datetime}.txt")
        output_log_file = os.path.join(properties['output_log_file_path'], f"AIP_Analysis_Log_{current_datetime}.log")

        # Create a logger
        logger = logging.getLogger()
        
        # Configure the logger to append to the specified log file
        handler = logging.FileHandler(output_log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO) 

        with open(output_csv_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ApplicationName', 'Status', 'Reason'])

        with open(output_txt_file, 'w', newline='') as txtfile:
            writer = csv.writer(txtfile)
            writer.writerow(['ApplicationName', 'Status', 'Reason'])

        # Read applications from file
        applications = []
        with open(applications_file, 'r') as file:
            for line in file:
                app_name, app_domain, source_code = line.strip().split(':')
                if app_name == 'application_name' and app_domain == 'domain_name':
                    continue
                else:
                    applications.append((app_name.strip(), app_domain.strip(), source_code.strip()))

        # Create batches
        batches = create_batches(applications, max_batches)
        num_of_apps = len(applications)
        num_of_batches = len(batches)
        print(f"{num_of_apps} Applications divided into {num_of_batches} Batches.\n")
        logger.info(f"{num_of_apps} Applications divided into {num_of_batches} Batches.\n")

        for count,app_batch in enumerate(batches, start=1):
            print(f"Batch-{count} {app_batch}\n")
            logger.info(f"Batch-{count} {app_batch}\n")

        # Process batches
        process_batch(batches, console_url, console_api_key, console_cli, source_code_path, logger, output_csv_file, output_txt_file)

    except Exception as e:
        print("Error:", e, "\n")
        try:
            logger.error("Error:", e, "\n")
        except Exception:
            pass

def step_2_download_missing_code_db_postgresql():
    """Step 2: Download missing code & DB from PostgreSQL using queries"""
    print("Step 2: Downloading missing code & DB from PostgreSQL...\n")

    # Dependency checks
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is required for Step 2. Please install with: pip install psycopg2-binary")
    if pd is None:
        raise RuntimeError("pandas is required for Step 2. Please install with: pip install pandas openpyxl")

    # Read properties
    properties = read_properties_file('config.properties')

    # Validate Step 2 specific properties without impacting Step 1
    required_params = [
        'pg_host', 'pg_port', 'pg_database', 'pg_user', 'pg_password',
        'domain_name', 'output_excel_file_path'
    ]
    missing_params = [p for p in required_params if p not in properties]
    if missing_params:
        raise ValueError(f"Missing required config properties for Step 2: {', '.join(missing_params)}")

    pg_host = properties['pg_host']
    pg_port = int(properties['pg_port'])
    pg_database = properties['pg_database']
    pg_user = properties['pg_user']
    pg_password = properties['pg_password']
    domain_name = properties['domain_name']
    output_dir = properties['output_excel_file_path']

    os.makedirs(output_dir, exist_ok=True)

    # Connect to PostgreSQL
    print("Connecting to PostgreSQL...")
    connection = psycopg2.connect(
        host=pg_host,
        port=pg_port,
        dbname=pg_database,
        user=pg_user,
        password=pg_password,
    )
    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            # Fetch application schema prefixes for the given domain
            print(f"Fetching application schemas for domain: {domain_name}")
            app_query = (
                "select c.schema_prefix\n"
                "from control_panel.domain d, control_panel.application a, control_panel.connection_profile c\n"
                "where d.name = %s\n"
                "and d.guid = a.domain_guid\n"
                "and a.connection_profile_guid = c.guid"
            )
            cursor.execute(app_query, (domain_name,))
            rows = cursor.fetchall()

        schema_prefixes: List[str] = [r[0] for r in rows]
        if not schema_prefixes:
            print(f"No applications found for domain '{domain_name}'. Nothing to export.\n")
            return

        print(f"Found {len(schema_prefixes)} application(s) for domain '{domain_name}'.")

        # Prepare containers for aggregated results
        missing_code_records: List[dict] = []
        missing_db_records: List[dict] = []

        # Queries (without schema prefix; we will set search_path per app)
        missing_code_sql = (
            "select distinct c1.file_path as \"Referenced File\","
            "c2.object_name as \"Missing Object Name\"," 
            "c2.object_type_str as \"Missing Object Type\"\n"
            "from cdt_objects c2,csv_file_objects c1,ctv_links ctv\n"
            "where c2.object_fullname like '%Unknown%'\n"
            "and c1.object_id = ctv.caller_id\n"
            "and c2.object_id = ctv.called_id\n"
            "and c2.object_type_str not like 'Cobol Directory'"
        )

        missing_db_sql = (
            "SELECT c1.object_name AS \"Missing Object Name\", "
            "MIN(c1.object_id) AS object_id, "
            "MIN(c1.object_type_str) AS \"Missing Object Type\", "
            "MIN(c2.file_path) AS db_obj_src_file "
            "FROM cdt_objects c1 "
            "JOIN ctv_links ctv ON ctv.called_id = c1.object_id "
            "JOIN csv_file_objects c2 ON ctv.caller_id = c2.object_id "
            "WHERE c1.object_type_str LIKE 'Missing%' "
            "GROUP BY c1.object_name"
        )

        # Iterate over each application schema
        for idx, schema_prefix in enumerate(schema_prefixes, start=1):
            app_schema_local = f"{schema_prefix}_local"
            print(f"[{idx}/{len(schema_prefixes)}] Processing schema: {app_schema_local}")
            try:
                with connection.cursor() as cursor:
                    # SET search_path safely using identifiers
                    cursor.execute(sql.SQL("SET search_path TO {};").format(sql.Identifier(app_schema_local)))

                    # Missing code
                    cursor.execute(missing_code_sql)
                    code_rows = cursor.fetchall()
                    colnames = [desc[0] for desc in cursor.description] if cursor.description else []
                    for row in code_rows:
                        record = {colnames[i]: row[i] for i in range(len(row))}
                        record['Application'] = schema_prefix
                        record['Schema'] = app_schema_local
                        missing_code_records.append(record)

                    # Missing DB
                    cursor.execute(missing_db_sql)
                    db_rows = cursor.fetchall()
                    colnames = [desc[0] for desc in cursor.description] if cursor.description else []
                    for row in db_rows:
                        record = {colnames[i]: row[i] for i in range(len(row))}
                        record['Application'] = schema_prefix
                        record['Schema'] = app_schema_local
                        missing_db_records.append(record)

            except Exception as app_err:
                print(f"  Error processing schema '{app_schema_local}': {app_err}")
                continue

        # Build DataFrames
        code_df = pd.DataFrame(missing_code_records)
        db_df = pd.DataFrame(missing_db_records)

        # Ensure stable column order
        if not code_df.empty:
            code_cols = ['Application', 'Schema'] + [c for c in code_df.columns if c not in ('Application', 'Schema')]
            code_df = code_df[code_cols]
        else:
            code_df = pd.DataFrame(columns=['Application', 'Schema', 'Referenced File', 'Missing Object Name', 'Missing Object Type'])

        if not db_df.empty:
            db_cols = ['Application', 'Schema'] + [c for c in db_df.columns if c not in ('Application', 'Schema')]
            db_df = db_df[db_cols]
        else:
            db_df = pd.DataFrame(columns=['Application', 'Schema', 'Missing Object Name', 'Missing Object Type', 'db_obj_src_file'])

        # Write to single Excel
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        safe_domain_for_file = re.sub(r'[^a-zA-Z0-9_-]+', '_', domain_name)
        excel_path = os.path.join(output_dir, f"MissingCode_MissingDB_forDomain_{safe_domain_for_file}.xlsx")

        print(f"Writing results to Excel: {excel_path}")
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Also include the list of application schema prefixes for traceability
            pd.DataFrame({
                'Application': schema_prefixes,
                'Schema': [f"{sp}_local" for sp in schema_prefixes],
            }).to_excel(writer, sheet_name='Applications', index=False)

            code_df.to_excel(writer, sheet_name='Missing_Code', index=False)
            db_df.to_excel(writer, sheet_name='Missing_DB', index=False)

        print("Step 2 completed.\n")
    finally:
        try:
            connection.close()
        except Exception:
            pass

def step_3_generate_app2app_dependency_neo4j():
    """Step 3: Generate App2App dependency and download results using neo4j query"""
    print("Step 3: Generating App2App dependency using Neo4j...")
    
    # Dependency checks
    if GraphDatabase is None:
        raise RuntimeError("neo4j is required for Step 3. Please install with: pip install neo4j")
    if pd is None:
        raise RuntimeError("pandas is required for Step 3. Please install with: pip install pandas openpyxl")
    
    # Read properties for Neo4j connection and output path
    try:
        properties = read_properties_file('config.properties')
        
        # Neo4j connection parameters from config
        neo4j_uri = properties.get('neo4j_uri', 'bolt://localhost:7697')
        neo4j_username = properties.get('neo4j_username', 'neo4j')
        neo4j_password = properties.get('neo4j_password', 'imaging')
        database_name = properties.get('neo4j_database', '')  # Leave empty for default
        
        output_dir = properties.get('output_excel_file_path', '.')
        
        # Validate required Neo4j parameters
        if not neo4j_uri or not neo4j_username or not neo4j_password:
            raise ValueError("Missing required Neo4j configuration parameters. Please check neo4j_uri, neo4j_username, and neo4j_password in config.properties")
        
    except Exception as e:
        print(f"Error reading config file: {e}")
        print("Using default Neo4j connection parameters...")
        neo4j_uri = 'bolt://localhost:7697'
        neo4j_username = 'neo4j'
        neo4j_password = 'imaging'
        database_name = ''
        output_dir = '.'
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Neo4j query for App2App dependencies
    app2app_query = """
    MATCH (o1{SosObject: true})
    WHERE (o1:Object OR o1:SubObject)
    MATCH (o1)-[r:SOS {systemLevel: 1, falseLink: false}]-(o2 {SosObject: true})
    WHERE (o2:Object OR o2:SubObject) AND o1 <> o2
    RETURN DISTINCT 
       CASE WHEN (o1)-[r]->(o2) THEN o1.FullName ELSE o2.FullName END AS SourceFullName, 
       CASE WHEN (o1)-[r]->(o2) THEN o1.Name ELSE o2.Name END AS SourceName, 
       CASE WHEN (o1)-[r]->(o2) THEN o1.Type ELSE o2.Type END AS SourceType, 
       CASE WHEN (o1)-[r]->(o2) THEN o1.Application ELSE o2.Application END AS SourceApplication, 
       CASE WHEN (o1)-[r]->(o2) THEN '->' ELSE '<-' END AS linkDirection, 
       r.sosProtocol AS Protocol, 
       r.sosTechno AS Technology, 
       CASE WHEN (o1)-[r]->(o2) THEN o2.FullName ELSE o1.FullName END AS TargetFullName, 
       CASE WHEN (o1)-[r]->(o2) THEN o2.Name ELSE o1.Name END AS TargetName, 
       CASE WHEN (o1)-[r]->(o2) THEN o2.Type ELSE o1.Type END AS TargetType, 
       CASE WHEN (o1)-[r]->(o2) THEN o2.Application ELSE o1.Application END AS TargetApplication
    ORDER BY SourceApplication
    """
    
    try:
        print(f"Connecting to Neo4j at: {neo4j_uri}")
        print(f"Username: {neo4j_username}")
        print(f"Database: {database_name if database_name else 'default'}")
        
        # Create Neo4j driver
        if neo4j_uri.startswith("http://"):
            # Convert HTTP URI to bolt URI for the driver
            bolt_uri = neo4j_uri.replace("http://", "bolt://")
        else:
            bolt_uri = neo4j_uri
            
        driver = GraphDatabase.driver(bolt_uri, auth=(neo4j_username, neo4j_password))
        
        # Test connection
        with driver.session(database=database_name) as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            print(f"Neo4j connection successful. Test query returned: {test_value}")
        
        # Execute the App2App dependency query
        print("Executing App2App dependency query...")
        with driver.session(database=database_name) as session:
            result = session.run(app2app_query)
            
            # Convert results to list of dictionaries
            records = []
            for record in result:
                record_dict = {}
                for key in record.keys():
                    record_dict[key] = record[key]
                records.append(record_dict)
        
        print(f"Query executed successfully. Retrieved {len(records)} dependency records.")
        
        if not records:
            print("No dependency records found. Creating empty Excel file.")
            # Create empty DataFrame with expected columns
            df = pd.DataFrame(columns=[
                'SourceFullName', 'SourceName', 'SourceType', 'SourceApplication',
                'linkDirection', 'Protocol', 'Technology',
                'TargetFullName', 'TargetName', 'TargetType', 'TargetApplication'
            ])
        else:
            # Convert to DataFrame
            df = pd.DataFrame(records)
        
        # Generate Excel file
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        excel_filename = f"App2App_Dependencies.xlsx"
        excel_path = os.path.join(output_dir, excel_filename)
        
        print(f"Generating Excel file: {excel_path}")
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Main dependency data
            df.to_excel(writer, sheet_name='App2App_Dependencies', index=False)
            
            # Summary statistics
            if not df.empty:
                summary_data = {
                    'Metric': [
                        'Total Dependencies',
                        'Unique Source Applications',
                        'Unique Target Applications',
                        'Unique Protocols',
                        'Unique Technologies'
                    ],
                    'Count': [
                        len(df),
                        df['SourceApplication'].nunique(),
                        df['TargetApplication'].nunique(),
                        df['Protocol'].nunique() if 'Protocol' in df.columns else 0,
                        df['Technology'].nunique() if 'Technology' in df.columns else 0
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary_Statistics', index=False)
                
                # Application dependency matrix
                if 'SourceApplication' in df.columns and 'TargetApplication' in df.columns:
                    app_matrix = df.groupby(['SourceApplication', 'TargetApplication']).size().reset_index(name='Dependency_Count')
                    app_matrix.to_excel(writer, sheet_name='Application_Matrix', index=False)
        
        print(f"Excel file generated successfully: {excel_path}")
        print(f"Total dependencies found: {len(records)}")
        
        # Display sample of results
        if records:
            print("\nSample of dependency records:")
            print("-" * 80)
            for i, record in enumerate(records[:5]):  # Show first 5 records
                print(f"Record {i+1}:")
                for key, value in record.items():
                    print(f"  {key}: {value}")
                print()
        
        print("Step 3 completed successfully.\n")
        
    except Exception as e:
        print(f"Error in Step 3: {e}")
        raise
    finally:
        try:
            if 'driver' in locals():
                driver.close()
                print("Neo4j connection closed.")
        except Exception as e:
            print(f"Warning: Error closing Neo4j connection: {e}")

def step_4_compare_edit_missing_code_vs_neo4j():
	"""Step 4: Prepare Missing Code Data"""
	print("Step 4: Prepare Missing Code Data...")

	if pd is None:
		raise RuntimeError("pandas is required for Step 4. Please install with: pip install pandas openpyxl")

	# Read configuration to discover file locations
	properties = read_properties_file('config.properties')
	output_dir = properties.get('output_excel_file_path', '.')
	domain_name = properties.get('domain_name', '')
	safe_domain_for_file = re.sub(r'[^a-zA-Z0-9_-]+', '_', domain_name)

	# Expected file paths from Steps 2 and 3
	missing_code_db_path = os.path.join(output_dir, f"MissingCode_MissingDB_forDomain_{safe_domain_for_file}.xlsx")
	neo4j_path = os.path.join(output_dir, "App2App_Dependencies.xlsx")

	print(f"Loading Missing Code/DB from: {missing_code_db_path}")
	print(f"Loading Neo4j dependencies from: {neo4j_path}")

	if not os.path.exists(missing_code_db_path):
		raise FileNotFoundError(f"Missing file: {missing_code_db_path}")
	if not os.path.exists(neo4j_path):
		raise FileNotFoundError(f"Missing file: {neo4j_path}")

	# Load sheets
	with pd.ExcelFile(missing_code_db_path) as xls:
		sheet_names = xls.sheet_names
		sheets = {name: pd.read_excel(xls, sheet_name=name) for name in sheet_names}
		missing_code_df = sheets.get('Missing_Code', pd.DataFrame())

	neo4j_df = pd.read_excel(neo4j_path, sheet_name='App2App_Dependencies')

	if missing_code_df.empty:
		print("Warning: 'Missing_Code' sheet is empty or not found. Nothing to edit.")
		return

	if neo4j_df.empty:
		print("Warning: Neo4j dependency sheet is empty. Nothing to compare.")
		return

	# 1) Remove rows where linkDirection contains left arrow (either '<-' or '←')
	if 'linkDirection' in neo4j_df.columns:
		before_rows = len(neo4j_df)
		def _normalize_direction(val: object) -> str:
			text = str(val)
			# Remove whitespace and control chars
			text = re.sub(r"\s+", "", text)
			text = re.sub(r"[\u2000-\u200F\u2028-\u202F\u2060\uFEFF]", "", text)
			return text
		ld_compact = neo4j_df['linkDirection'].map(_normalize_direction)
		left_arrow_mask = ld_compact.str.contains("<-", na=False) | ld_compact.str.contains("←", na=False)
		neo4j_df = neo4j_df[~left_arrow_mask]
		after_rows = len(neo4j_df)
		print(f"Filtered Neo4j dependencies: removed {before_rows - after_rows} left-arrow link rows")
	else:
		print("Warning: 'linkDirection' column not found in Neo4j data; skipping left-arrow filter")

	try:
		with pd.ExcelWriter(neo4j_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
			neo4j_df.to_excel(writer, sheet_name='App2App_Dependencies', index=False)
		print("Updated Neo4j Excel with filtered dependencies (removed left-arrow rows).")
	except Exception as _e:
		print(f"Warning: Could not update Neo4j Excel: {_e}")

	# 2) Normalize TargetType: any 'Cobol ... Program' -> 'Cobol Program'
	if 'TargetType' in neo4j_df.columns:
		def _normalize_cobol_program(value: object) -> object:
			text = str(value)
			if re.search(r"^\s*Cobol\b.*\bProgram\s*$", text, flags=re.IGNORECASE):
				return "Cobol Program"
			return value
		neo4j_df['TargetType'] = neo4j_df['TargetType'].map(_normalize_cobol_program)
	else:
		print("Warning: 'TargetType' column not found in Neo4j data; skipping Cobol normalization")

	try:
		with pd.ExcelWriter(neo4j_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
			neo4j_df.to_excel(writer, sheet_name='App2App_Dependencies', index=False)
		print("Updated Neo4j Excel with normalized TargetType.")
	except Exception as _e:
		print(f"Warning: Could not update Neo4j Excel: {_e}")

	# 3) Build comparison keys
	# Missing Code columns may be named either 'Missing Code Object' or 'Missing Object Name'
	missing_name_col = None
	for candidate in ['Missing Code Object', 'Missing Object Name']:
		if candidate in missing_code_df.columns:
			missing_name_col = candidate
			break
	if missing_name_col is None:
		raise KeyError("Neither 'Missing Code Object' nor 'Missing Object Name' column found in 'Missing_Code' sheet")

	missing_type_col = None
	for candidate in ['Missing Object Type']:
		if candidate in missing_code_df.columns:
			missing_type_col = candidate
			break
	if missing_type_col is None:
		raise KeyError("'Missing Object Type' column not found in 'Missing_Code' sheet")

	# Normalize Missing Object Type values by removing leading 'Unknown ' prefix
	def _strip_unknown_prefix(value: object) -> str:
		text = str(value)
		text = re.sub(r'^\s*Unknown\s+', '', text, flags=re.IGNORECASE)
		return text.strip()
	missing_code_df[missing_type_col] = missing_code_df[missing_type_col].map(_strip_unknown_prefix)
     
    # # Normalize Missing Object Type values by removing leading 'Cobol Transactions to Cobol Program ' prefix
	# def _strip_unknown_prefix(value: object) -> str:
	# 	text = str(value)
	# 	text = re.sub(r'^\s*Unknown\s+', '', text, flags=re.IGNORECASE)
	# 	return text.strip()
	# missing_code_df[missing_type_col] = missing_code_df[missing_type_col].map(_strip_unknown_prefix)

	if 'TargetName' not in neo4j_df.columns or 'TargetType' not in neo4j_df.columns:
		raise KeyError("'TargetName' and/or 'TargetType' columns not found in Neo4j data")

	# Prepare clean keys (strip only, exact match otherwise)
	def _clean_text(v: object) -> str:
		return str(v).strip()

	neo4j_keys = set(zip(neo4j_df['TargetName'].map(_clean_text), neo4j_df['TargetType'].map(_clean_text)))
	missing_pairs = list(zip(missing_code_df[missing_name_col].map(_clean_text), missing_code_df[missing_type_col].map(_clean_text)))

	# Identify rows to drop in Missing_Code
	to_keep_mask = [pair not in neo4j_keys for pair in missing_pairs]
	removed_count = len(missing_pairs) - sum(to_keep_mask)

	if removed_count == 0:
		print("No exact matches found between Missing Code and Neo4j data. No rows removed.")
		filtered_missing_code_df = missing_code_df.reset_index(drop=True)
	else:
		filtered_missing_code_df = missing_code_df[to_keep_mask].reset_index(drop=True)
		print(f"Removing {removed_count} matching row(s) from 'Missing_Code' sheet")

	# 4) Overwrite Missing_Code in the Step 2 workbook, preserving other sheets
	sheets['Missing_Code'] = filtered_missing_code_df
	with pd.ExcelWriter(missing_code_db_path, engine='openpyxl') as writer:
		for name, df in sheets.items():
			# Ensure DataFrame even if None
			if df is None:
				df = pd.DataFrame()
			df.to_excel(writer, sheet_name=name, index=False)

	print("Step 4 completed successfully.\n")

def step_5_compare_edit_missing_db_vs_neo4j():
    """Step 5: Prepare Missing DB Data"""
    print("Step 5: Prepare Missing DB Data...")

    if pd is None:
        raise RuntimeError("pandas is required for Step 5. Please install with: pip install pandas openpyxl")

    # Read configuration
    properties = read_properties_file('config.properties')
    output_dir = properties.get('output_excel_file_path', '.')
    domain_name = properties.get('domain_name', '')
    safe_domain_for_file = re.sub(r'[^a-zA-Z0-9_-]+', '_', domain_name)

    # Parse TargetApplication list
    raw_list = properties.get('TargetApplicationList', '')
    target_apps: List[str] = []
    if raw_list:
        try:
            target_apps = ast.literal_eval(raw_list)
            if not isinstance(target_apps, list):
                target_apps = []
        except Exception:
            # Support comma-separated fallback e.g., A,B,C
            target_apps = [t.strip() for t in re.split(r'[;,]', raw_list) if t.strip()]

    # File paths
    missing_code_db_path = os.path.join(output_dir, f"MissingCode_MissingDB_forDomain_{safe_domain_for_file}.xlsx")
    neo4j_path = os.path.join(output_dir, "App2App_Dependencies.xlsx")

    print(f"Loading Missing DB from: {missing_code_db_path}")
    print(f"Loading Neo4j dependencies from: {neo4j_path}")

    if not os.path.exists(missing_code_db_path):
        raise FileNotFoundError(f"Missing file: {missing_code_db_path}")
    if not os.path.exists(neo4j_path):
        raise FileNotFoundError(f"Missing file: {neo4j_path}")

    # Load Missing_DB and other sheets to preserve
    with pd.ExcelFile(missing_code_db_path) as xls:
        sheet_names = xls.sheet_names
        sheets = {name: pd.read_excel(xls, sheet_name=name) for name in sheet_names}
        missing_db_df = sheets.get('Missing_DB', pd.DataFrame())

    if missing_db_df.empty:
        print("Warning: 'Missing_DB' sheet is empty or not found. Nothing to edit.")
        return

    neo4j_df = pd.read_excel(neo4j_path, sheet_name='App2App_Dependencies')
    if neo4j_df.empty:
        print("Warning: Neo4j dependency sheet is empty. Nothing to compare.")
        return

    # Validate required columns
    if 'TargetApplication' not in neo4j_df.columns:
        raise KeyError("'TargetApplication' column not found in Neo4j data")
    if 'TargetName' not in neo4j_df.columns:
        raise KeyError("'TargetName' column not found in Neo4j data")

    missing_name_col = None
    for candidate in ['Missing Object Name']:
        if candidate in missing_db_df.columns:
            missing_name_col = candidate
            break
    if missing_name_col is None:
        raise KeyError("'Missing Object Name' column not found in 'Missing_DB' sheet")

    # Filter Neo4j to selected TargetApplication values if provided
    if target_apps:
        filtered_neo4j_df = neo4j_df[neo4j_df['TargetApplication'].astype(str).isin([str(a) for a in target_apps])]
        print(f"Filtered Neo4j by TargetApplication list: kept {len(filtered_neo4j_df)} of {len(neo4j_df)} rows")
    else:
        filtered_neo4j_df = neo4j_df
        print("No TargetApplication list provided; using all Neo4j rows")

    # Build exact-match set of TargetName
    def _clean_text(v: object) -> str:
        return str(v).strip()

    neo4j_target_names = set(filtered_neo4j_df['TargetName'].map(_clean_text))
    missing_names = missing_db_df[missing_name_col].map(_clean_text)

    to_keep_mask = ~missing_names.isin(neo4j_target_names)
    removed_count = (~to_keep_mask).sum()

    if removed_count == 0:
        print("No exact matches found between Missing DB and Neo4j data. No rows removed.")
        filtered_missing_db_df = missing_db_df.reset_index(drop=True)
    else:
        filtered_missing_db_df = missing_db_df[to_keep_mask].reset_index(drop=True)
        print(f"Removing {int(removed_count)} matching row(s) from 'Missing_DB' sheet")

    # Overwrite Missing_DB in the workbook, preserving other sheets
    sheets['Missing_DB'] = filtered_missing_db_df
    with pd.ExcelWriter(missing_code_db_path, engine='openpyxl') as writer:
        for name, df in sheets.items():
            if df is None:
                df = pd.DataFrame()
            df.to_excel(writer, sheet_name=name, index=False)

    print("Step 5 completed successfully.\n")

# Removed old Step 6 and Step 7 per new step structure (only 1–5)

def prompt_and_run_additional_steps():
    steps = {
        '1': ("Onboard applications onto AIP Console", step_1_run_aip_analysis),
        '2': ("Download missing code & DB from PostgreSQL", step_2_download_missing_code_db_postgresql),
        '3': ("Generate App2App dependency using Neo4j", step_3_generate_app2app_dependency_neo4j),
        '4': ("Prepare Missing Code Data", step_4_compare_edit_missing_code_vs_neo4j),
        '5': ("Prepare Missing DB Data", step_5_compare_edit_missing_db_vs_neo4j),
    }

    print("\n" + "="*60)
    print("STEP SELECTION MENU")
    print("="*60)
    print("Enter step numbers to run (comma-separated):")
    print()
    for key in sorted(steps.keys(), key=lambda k: int(k)):
        print(f"  {key}. {steps[key][0]}")
    print("="*60)

    user_input = input("\nSteps: ").strip()
    if not user_input:
        print("No additional steps selected. Exiting.\n")
        return

    selected = []
    for token in re.split(r'[\s,]+', user_input):
        token = token.strip()
        if token and token in steps and token not in selected:
            selected.append(token)

    if not selected:
        print("No valid steps selected. Exiting.\n")
        return

    print(f"\nExecuting {len(selected)} selected step(s): {', '.join(selected)}")
    print("-" * 60)
    
    for token in selected:
        title, func = steps[token]
        print(f"\nExecuting Step {token}: {title}")
        print("-" * 40)
        try:
            func()
        except Exception as e:
            print(f"Error executing Step {token}: {e}")
        print("-" * 40)

def main():
    print("="*60)
    print("AIP AUTOMATION TOOL - STEP EXECUTION")
    print("="*60)
    prompt_and_run_additional_steps()
    print("\nAll selected steps completed. Exiting.\n")

if __name__ == "__main__":
    main()
