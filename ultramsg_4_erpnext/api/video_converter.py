import frappe
import os
import subprocess
import logging
import requests
from werkzeug.utils import secure_filename

# Configure logging to the terminal
logging.basicConfig(level=logging.DEBUG)

@frappe.whitelist(allow_guest=True)
def convert_to_mp4(file_url=None):
    print("convert_to_mp4 function called")
    logging.debug("convert_to_mp4 function called")

    try:
        if file_url:
            print(f"Received file URL: {file_url}")
            logging.debug(f"Received file URL: {file_url}")

            response = requests.get(file_url)
            if response.status_code != 200:
                print(f"Failed to download file from URL: {file_url}")
                logging.error(f"Failed to download file from URL: {file_url}")
                return {'error': "Failed to download file from URL"}, 400
            
            filename = file_url.split("/")[-1]
            input_path = os.path.join('/tmp', filename)
            output_filename = os.path.splitext(filename)[0] + '.mp4'
            output_path = os.path.join(frappe.get_site_path('public', 'files'), output_filename)

            # Save the downloaded content as a file temporarily
            with open(input_path, 'wb') as f:
                f.write(response.content)
            print(f"File saved to: {input_path}")
            logging.debug(f"File saved to: {input_path}")
        else:
            print("No file or file URL in the request")
            logging.error("No file or file URL in the request")
            return {'error': "No file or file URL provided"}, 400

        # Re-encode the video and audio to formats compatible with MP4
        command = ['ffmpeg', '-y', '-v', 'verbose', '-i', input_path, '-c:v', 'libx264', '-c:a', 'aac', output_path]
        print(f"Running command: {' '.join(command)}")
        logging.debug(f"Running command: {' '.join(command)}")

        # Execute the command with a timeout
        process = subprocess.run(command, capture_output=True, text=True, timeout=120)

        print(f"ffmpeg stdout: {process.stdout}")
        print(f"ffmpeg stderr: {process.stderr}")
        logging.debug(f"ffmpeg stdout: {process.stdout}")
        logging.debug(f"ffmpeg stderr: {process.stderr}")

        if process.returncode != 0:
            error_message = f"ffmpeg error: {process.stderr}"
            print(error_message)
            logging.error(error_message)
            raise Exception(error_message)

        # Remove the temporary input file after conversion
        os.remove(input_path)

        # Return the full URL of the converted MP4 file
        site_url = frappe.utils.get_url()
        file_url = f'{site_url}/files/{output_filename}'
        print(f"Conversion successful, file saved to: {file_url}")
        logging.debug(f"Conversion successful, file saved to: {file_url}")
        

        return  {'file_url': file_url}


    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        logging.error(f"Exception occurred: {str(e)}")
        frappe.log_error(message=str(e), title="Video Conversion Error")
        return {'error': str(e)}, 500
