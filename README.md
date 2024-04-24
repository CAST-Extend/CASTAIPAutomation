
### **CASTAIPAutomation**

####  **Purpose:**
The purpose of the script is to automate the analysis of multiple applications using CAST Imaging-Console. It streamlines the process of analyzing source code files for various applications, allowing users to specify configurations, define source paths, and customize analysis parameters through a configuration file. 

#### **Key objectives and functionalities of the script include:**
1.	**Automation**: The script automates the process of analyzing multiple applications by interfacing with the CAST Imaging-Console via command-line execution. It eliminates the need for manual intervention in initiating and monitoring the analysis process for each application.
2.	**Batch Processing**: Applications are grouped into batches, and each batch is processed concurrently, leveraging multi-threading to improve efficiency. This enables faster analysis of a large number of applications, enhancing overall productivity.
3.	**Configurability**: Users can customize various parameters such as source paths, server URLs, authentication api-key, and batch sizes through the config.properties file. This allows flexibility in adapting the script to different environments and analysis requirements.
4.	**Error Handling**: The script incorporates error handling mechanisms to detect and handle issues during the analysis process. It logs detailed error messages, including return codes from the Console CLI, facilitating troubleshooting and debugging.
5.	**Output Generation**: Upon completion of analysis for each application, the script generates a AIP_Analysis CSV file and txt files containing the application names, status, reasons for success or failure. Additionally, detailed log files are providing comprehensive insights into the analysis execution.
Overall, the script aims to streamline and automate the process of application analysis, improving efficiency, accuracy, and ease of management for software development and quality assurance teams. By abstracting the complexities of manual analysis tasks and providing a configurable and scalable solution, it empowers users to perform thorough and consistent analysis across multiple applications with minimal effort.
 
#### **Prerequisites:**
1.	**Java Development Kit (JDK**): Ensure that JDK is installed and configured properly on the system.
2.	**Python**: Install Python programming language (version 3.x) on the system.
3.	**AIP Imaging-Console**: Make sure AIP Imaging-Console is installed and set the Source Folder Location.
4.	**AIP Console Tools CLI**: Obtain the AIP Console Tools and ensure aip-console-tools-cli.jar file is accessible.
5.	**Internet Connectivity**: Ensure the system has internet connectivity for accessing URLs specified in the configuration.
6.	**Configuration File**: Prepare a configuration file named config.properties with necessary parameters (details in the Configuration section).

#### **Installation:**
1.	**Clone Repository**: Clone the repository containing the script to the local system.
2.	**Setup Environment**: Set up the Python environment and install required libraries using pip install -r requirements.txt.
3.	**Configuration**: Configure the config.properties file with relevant paths and parameters (details in the Configuration section).
4.	**Prepare Input Data**: Prepare a application.txt file containing the list of applications to be analyzed, with each entry in the format application_name:domain_name.

#### **Usage:**
1.	**Execute Script**: Run the script by executing python AIP_Automation.py.
2.	**Monitor Progress**: Monitor the console for progress updates on application analysis.
3.	**Review Logs**: Check the log files generated in the specified log folder for detailed information about the analysis process.

### **Configuration:**
Ensure the config.properties file is correctly configured with the following parameters:

- **console_url**: AIP Imaging-Console URL for server communication.
- **console_api_key**: AIP Imaging-Console api-key for Authentication..
- **console_cli_path**: Path to the directory containing the aip-console-tools-cli.jar file.
- **max_batches**: Maximum number of batches to process.
- **applications_file**: Path to the file containing the list of applications.
- **source_code_path**: Path to the directory containing the source code files of the applications to be analyzed.
- **output_csv_file_path**: Path to the folder where output csv files will be stored.
- **output_txt_file_path**: Path to the folder where output txt files will be stored.
- **output_log_file_path**: Path to the folder where log files will be stored.


#### **Output:**
1.	**AIP Analysis CSV File**: A CSV file containing the summary of the analysis results.
2.	**AIP Analysis TXT File**: A TXT file containing the summary of the analysis results.
3.	**AIP Analysis Log File**: Detailed log files are generated for each execution of script and stored in the specified log folder.

#### **Sample Usage:**

- Copy code
- python AIP_Automation.py

#### **Troubleshooting:**
- Ensure all paths specified in the configuration file are correct and accessible.
- Check internet connectivity if accessing external URLs.
- Review log files for detailed error messages and troubleshooting steps.

#### **Notes:**
- This script supports multi-threading for efficient processing of application batches.
- Ensure proper permissions are set for accessing directories and executing files specified in the configuration.
