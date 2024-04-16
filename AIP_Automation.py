import os
import subprocess
import csv
import datetime
import math
import threading
import logging

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
    print(f"Reading properties from file: {filename}")
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
            print(f"Program stopped because required parameter '{param}' is not in the config.properties")
            raise ValueError(f"Required parameter '{param}' is not in the config.properties")

# Function to process application
def process_application(app_batch, console_url, console_api_key, console_cli, source_code_path, logger, output_csv_file, output_txt_file):
    try:
        print(f"Executing Batch: {app_batch}")
        logger.info(f"Executing Batch: {app_batch}")
        for app_name, app_domain in app_batch:
            command = [
                'java', '-jar', f'{console_cli}',
                'add',
                '-n', f'{app_name}',
                '--domain-name', f'{app_domain}',
                '-f', f'{source_code_path}/{app_name}',
                '-s',  f'{console_url}',
                '--apikey', f'{console_api_key}',
                '--verbose',
                '--auto-create',
                'Publish-Imaging',
                '--upload-application=true',
                '--exclude-patterns="tmp/, temp/, *test, tests, target/, .svn/, .git/, _Macosx/, test/"'
            ]
            print(f"Executing command for Application-{app_name} to run AIP Analysis:", " ".join(command))
            # logger.info("Executing command:", " ".join(command))

            completed_process = subprocess.run(command, capture_output=True, text=True)
            return_code = completed_process.returncode
            if return_code == 0:
                command_2 = [
                    'java', '-jar', f'{console_cli}',
                    'Publish-Imaging',
                    '-n', f'{app_name}',
                    '-s',  f'{console_url}',
                    '--apikey', f'{console_api_key}',
                    '--verbose'
                ]
                print(f"Executing command for Application-{app_name} for Imaging upload:", " ".join(command_2))
                # logger.info("Executing command:", " ".join(command))

                completed_process_2 = subprocess.run(command_2, capture_output=True, text=True)
                return_code_2 = completed_process_2.returncode

                if return_code_2 == 0:
                    status = "Passed"
                    reason = "Application processed successfully"
                    print(f'Application - {app_name} processed successfully\n')
                    logger.info(f'Application - {app_name} processed successfully\n')
                else:
                    status = "Failed"
                    reason = return_code_messages.get(return_code, f"Unknown return code: {return_code}")
                    print(f'Application - {app_name} Failed with Unknown return code: {return_code}\n')
                    logger.info(f'Application - {app_name} Failed with Unknown return code: {return_code}\n') 

            else:
                status = "Failed"
                reason = return_code_messages.get(return_code, f"Unknown return code: {return_code}")
                print(f'Application - {app_name} Failed with Unknown return code: {return_code}\n')
                logger.info(f'Application - {app_name} Failed with Unknown return code: {return_code}\n')                

            # Write output data to CSV
            with open(output_csv_file, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([app_name, status, reason])

            # Write output data to text file
            with open(output_txt_file, 'a', newline='') as txtfile:
                txtfile.write(f"{app_name}: {status} - {reason}\n")

    except Exception as e:
        print("Error processing application:", e)
        logger.error("Error processing application:", e)

# Function to create batches
def create_batches(applications, max_batches):
    batch_size = math.ceil(len(applications) / max_batches)
    batches = [applications[i * batch_size:(i + 1) * batch_size] for i in range(max_batches)]
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

# Main function
def main():
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
                app_name, app_domain = line.strip().split(':')
                if app_name == 'application_name' and app_domain == 'domain_name':
                    continue
                else:
                    applications.append((app_name.strip(), app_domain.strip()))

        # Create batches
        batches = create_batches(applications, max_batches)

        # Process batches
        process_batch(batches, console_url, console_api_key, console_cli, source_code_path, logger, output_csv_file, output_txt_file)

    except Exception as e:
        print("Error:", e)
        logger.error("Error:", e)

if __name__ == "__main__":
    main()
