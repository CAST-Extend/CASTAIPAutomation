
### **CASTAIPAutomation**

####  **Purpose:**
The purpose of the script is to automate the analysis of multiple applications using CAST Imaging-Console. It streamlines the process of analyzing source code files for various applications, allowing users to specify configurations, define source paths, and customize analysis parameters through a configuration file. 

#### **Key objectives and functionalities of the script include:**
1.	**Automation**: The script automates the process of analyzing multiple applications by interfacing with the CAST Imaging-Console via command-line execution. It eliminates the need for manual intervention in initiating and monitoring the analysis process for each application.
2.	**Batch Processing**: Applications are grouped into batches, and each batch is processed concurrently, leveraging multi-threading to improve efficiency. This enables faster analysis of a large number of applications, enhancing overall productivity.
3.	**Configurability**: Users can customize various parameters such as source paths, server URLs, authentication api-key, and batch sizes through the config.properties file. This allows flexibility in adapting the script to different environments and analysis requirements.
4.	**Error Handling**: The script incorporates error handling mechanisms to detect and handle issues during the analysis process. It logs detailed error messages, including return codes from the Console CLI, facilitating troubleshooting and debugging.
5.	**Output Generation**: Upon completion of analysis for each application, the script generates a AIP_Analysis CSV file and txt files containing the application names, status, reasons for success or failure. Additionally, detailed log files are providing comprehensive insights into the analysis execution.
6.	**Neo4j Integration**: The script can connect to Neo4j databases to extract application-to-application dependencies and generate comprehensive Excel reports for analysis and comparison.
Overall, the script aims to streamline and automate the process of application analysis, improving efficiency, accuracy, and ease of management for software development and quality assurance teams. By abstracting the complexities of manual analysis tasks and providing a configurable and scalable solution, it empowers users to perform thorough and consistent analysis across multiple applications with minimal effort.
 
#### **Prerequisites:**
1.	**Java Development Kit (JDK**): Ensure that JDK is installed and configured properly on the system.
2.	**Python**: Install Python programming language (version 3.x) on the system.
3.	**AIP Imaging-Console**: Make sure AIP Imaging-Console is installed and set the Source Folder Location.
4.	**AIP Console Tools CLI**: Obtain the AIP Console Tools and ensure aip-console-tools-cli.jar file is accessible.
5.	**Internet Connectivity**: Ensure the system has internet connectivity for accessing URLs specified in the configuration.
6.	**Configuration File**: Prepare a configuration file named config.properties with necessary parameters (details in the Configuration section).
7.	**Neo4j Database**: For step 3 functionality, ensure Neo4j database is running and accessible (default: bolt://localhost:7687).
8.	**Python Dependencies**: Install required Python packages using `pip install -r requirements.txt`.

#### **Installation:**
1.	**Clone Repository**: Clone the repository containing the script to the local system.
2.	**Install Dependencies**: Install required Python packages: `pip install -r requirements.txt`
3.	**Configuration**: Configure the config.properties file with relevant paths and parameters (details in the Configuration section).
4.	**Prepare Input Data**: Prepare a application.txt file containing the list of applications to be analyzed, with each entry in the format application_name:domain_name.

#### **Usage:**
1.	**Execute Script**: Run the script by executing python AIP_Automation.py.
2.	**Select Steps**: Choose which steps to execute from the available options:
   - Step 1: Onboard applications onto AIP Console
   - Step 2: Download missing code & DB from PostgreSQL
   - Step 3: Generate App2App dependency using Neo4j
   - Step 4: Prepare Missing Code Data
   - Step 5: Prepare Missing DB Data
3.	**Monitor Progress**: Monitor the console for progress updates on application analysis.
4.	**Review Logs**: Check the log files generated in the specified log folder for detailed information about the analysis process.

### **Configuration:**
Ensure the config.properties file is correctly configured with the following parameters:

- **console_url**: AIP Imaging-Console URL for server communication.
- **console_api_key**: AIP Imaging-Console api-key for Authentication..
- **console_cli_path**: Path to the directory containing the aip-console-tools-cli.jar file(AIP Console Tools version shouble be same or near to AIP Console Version {In LM tested with Console v2.11.5 and Tool v2.11.6}).
- **max_batches**: Maximum number of batches to process.
- **applications_file**: Path to the file containing the list of applications.
- **source_code_path**: Path to the directory containing the source code files of the applications to be analyzed (this path should be same as Source Folder Location configured inside AIP Console).
- **output_csv_file_path**: Path to the folder where output csv files will be stored.
- **output_txt_file_path**: Path to the folder where output txt files will be stored.
- **output_log_file_path**: Path to the folder where log files will be stored.

**For Step 2 (PostgreSQL):**
- **pg_host**: PostgreSQL host address
- **pg_port**: PostgreSQL port number
- **pg_database**: PostgreSQL database name
- **pg_user**: PostgreSQL username
- **pg_password**: PostgreSQL password
- **domain_name**: Domain name for analysis
- **output_excel_file_path**: Path for Excel output files

**For Step 3 (Neo4j):**
- **neo4j_uri**: Neo4j database URI (default: bolt://localhost:7687)
- **neo4j_username**: Neo4j username (default: neo4j)
- **neo4j_password**: Neo4j password (default: imaging)
- **neo4j_database**: Neo4j database name (leave empty for default)
- **output_excel_file_path**: Path for Excel output files

**For Step 4 & Step 5 (Comparison settings):**
- **TargetApplicationList**: List of target applications to consider when comparing Missing DB with Neo4j data. Accepts a Python-style list or comma/semicolon-separated string.
  - Example (list): `TargetApplicationList = ['Database', 'AppX']`
  - Example (CSV): `TargetApplicationList = Database, AppX`

#### **Output:**
1.	**AIP Analysis CSV File**: A CSV file containing the summary of the analysis results.
2.	**AIP Analysis TXT File**: A TXT file containing the summary of the analysis results.
3.	**AIP Analysis Log File**: Detailed log files are generated for each execution of script and stored in the specified log folder.
4.	**Missing Code/DB Excel File**: Excel file with missing code and database information (Step 2).
5.	**App2App Dependencies Excel File**: Comprehensive Excel file with application-to-application dependencies including main data, summary statistics, and an application dependency matrix.

#### **Step details and data processing rules:**

- **Step 2 – Missing Code/DB extraction (PostgreSQL)**:
  - Produces workbook `MissingCode_MissingDB_forDomain_<domain>.xlsx` with sheets `Missing_Code` and `Missing_DB`.

- **Step 3 – App2App dependencies (Neo4j)**:
  - Produces workbook `App2App_Dependencies.xlsx` with sheet `App2App_Dependencies`.

- **Step 4 – Prepare Missing Code Data**:
  - Loads `Missing_Code` and Neo4j data.
  - Removes Neo4j rows where `linkDirection` contains a left arrow (`<-` or `←`).
  - Normalizes Neo4j `TargetType`: any variant like "Cobol Batch Program", "Cobol Transactional Program", etc., becomes "Cobol Program".
  - Normalizes `Missing_Code`.`Missing Object Type` by removing a leading "Unknown " prefix (e.g., "Unknown CICS Map" -> "CICS Map").
  - Compares `Missing_Code` by exact matches of (Name, Type):
    - Missing side: `Missing Code Object` or `Missing Object Name`, and `Missing Object Type`.
    - Neo4j side: `TargetName` and `TargetType`.
  - Deletes matching rows from `Missing_Code` and rewrites the workbook while preserving other sheets. If no matches are found, normalization is still saved.

- **Step 5 – Prepare Missing DB Data**:
  - Reads `TargetApplicationList` from `config.properties` to optionally limit the comparison to specific Neo4j `TargetApplication` values.
  - Loads `Missing_DB` and Neo4j data. If a list is provided, filters Neo4j rows to those `TargetApplication` values.
  - Compares `Missing_DB`.`Missing Object Name` to Neo4j `TargetName` (exact match, trimmed).
  - Deletes matching rows from `Missing_DB` and rewrites the workbook while preserving other sheets.

#### **Examples:**

```bash
python AIP_Automation.py
# Select steps: 2, 3, 4, 5 as needed
```

```properties
# config.properties (excerpts)
domain_name=OCAS
output_excel_file_path=C:\\work\\...\\output_files

# Neo4j
neo4j_uri=bolt://localhost:7687
neo4j_username=neo4j
neo4j_password=imaging

# Step 5 filtering
TargetApplicationList = ['Database']
```

#### **Sample Usage:**

- Copy code
- python AIP_Automation.py

**Testing Neo4j Connection:**
- To test only the Neo4j connection functionality: `python test_neo4j_connection.py`

#### **Troubleshooting:**
- Ensure all paths specified in the configuration file are correct and accessible.
- Check internet connectivity if accessing external URLs.
- Review log files for detailed error messages and troubleshooting steps.
- For Neo4j connection issues, verify the database is running and credentials are correct.
- Ensure all required Python packages are installed using `pip install -r requirements.txt`.
- Verify Neo4j connection parameters in config.properties: neo4j_uri, neo4j_username, neo4j_password.

#### **Notes:**
- This script supports multi-threading for efficient processing of application batches.
- Ensure proper permissions are set for accessing directories and executing files specified in the configuration.
- Step 3 requires Neo4j database access and will generate comprehensive dependency analysis reports.
- The script automatically handles connection management and resource cleanup for database connections.
