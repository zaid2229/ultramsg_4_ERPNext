import frappe
from frappe import _
from frappe.email.doctype.notification.notification import Notification, get_context, json
from frappe.core.doctype.role.role import get_info_based_on_role, get_user_info
import requests
import io
import base64
from frappe.utils import now
import time
from frappe import enqueue

# To send WhatsApp message and document using UltraMsg
class ERPGulfNotification(Notification):
  
    # To create PDF
    def create_pdf(self, doc):
        file = frappe.get_print(doc.doctype, doc.name, self.print_format, as_pdf=True)
        pdf_bytes = io.BytesIO(file)
        pdf_base64 = base64.b64encode(pdf_bytes.getvalue()).decode()
        in_memory_url = f"data:application/pdf;base64,{pdf_base64}"
        return in_memory_url

    # Fetch PDF from the create_pdf function and send to WhatsApp 
    @frappe.whitelist()
    def send_whatsapp_with_pdf(self, doc, context):
        memory_url = self.create_pdf(doc)
        token = frappe.get_doc('whatsapp message').get('token')
        msg1 = frappe.render_template(self.message, context)
        recipients = self.get_receiver_list(doc, context)
        
        multiple_numbers = [] 
        for receipt in recipients:
            number = receipt
            multiple_numbers.append(number)
        add_multiple_numbers_to_url = ','.join(multiple_numbers)
        document_url = frappe.get_doc('whatsapp message').get('url')
        payload = {
            'token': token,
            'to': add_multiple_numbers_to_url,
            "filename": doc.name,
            "document": memory_url,
            "caption": msg1,
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'} 
        try:
            time.sleep(10)
            response = requests.post(document_url, data=payload, headers=headers)
            if response.status_code == 200:
                response_json = response.json()
                if "sent" in response_json and response_json["sent"] == "true":
                    # Log success
                    current_time = now()  # for getting current time
                    msg1 = frappe.render_template(self.message, context)
                    frappe.get_doc({"doctype": "ultramsg_4_ERPNext log", "title": "WhatsApp message and PDF successfully sent", "message": msg1, "to_number": doc.custom_mobile_phone, "time": current_time}).insert()
                elif "error" in response_json:
                    # Log error
                    frappe.log("WhatsApp API Error: ", response_json.get("error"))
                else:
                    # Log unexpected response
                    frappe.log("Unexpected response from WhatsApp API")
            else:
                # Log HTTP error
                frappe.log("WhatsApp API returned a non-200 status code: ", str(response.status_code))
                return response
        except Exception as e:
            frappe.log_error(title='Failed to send notification', message=frappe.get_traceback())  

    # Send message without PDF
    def send_whatsapp_without_pdf(self, doc, context):
        token = frappe.get_doc('whatsapp message').get('token')
        message_url = frappe.get_doc('whatsapp message').get('message_url')
        msg1 = frappe.render_template(self.message, context)
        recipients = self.get_receiver_list(doc, context) 
        multiple_numbers = [] 
        for receipt in recipients:
            number = receipt
            multiple_numbers.append(number)
        add_multiple_numbers_to_url = ','.join(multiple_numbers)
        payload = {
            'token': token,
            'to': add_multiple_numbers_to_url,
            'body': msg1,
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        try:
            time.sleep(10)
            response = requests.post(message_url, data=payload, headers=headers)
            # When the message is successfully sent, its details are stored in ultramsg_4_ERPNext log  
            if response.status_code == 200:
                response_json = response.json()
                if "sent" in response_json and response_json["sent"] == "true":
                    # Log success
                    current_time = now()  # for getting current time
                    msg1 = frappe.render_template(self.message, context)
                    frappe.get_doc({"doctype": "ultramsg_4_ERPNext log", "title": "WhatsApp message successfully sent", "message": msg1, "to_number": doc.custom_mobile_phone, "time": current_time}).insert()
                elif "error" in response_json:
                    # Log error
                    frappe.log("WhatsApp API Error: ", response_json.get("error"))
                else:
                    # Log unexpected response
                    frappe.log("Unexpected response from WhatsApp API")
            else:
                # Log HTTP error
                frappe.log("WhatsApp API returned a non-200 status code: ", str(response.status_code))
            return response.text
        except Exception as e:
            frappe.log_error(title='Failed to send notification', message=frappe.get_traceback())  

    # Send message with video
    def send_whatsapp_with_video(self, doc, context):
        print(doc)
        token = frappe.get_doc('whatsapp message').get('token')
        video_url = frappe.get_doc('whatsapp message').get('video_url')
        msg1 = frappe.render_template(self.message, context)
        recipients = self.get_receiver_list(doc, context) 
        multiple_numbers = [] 
        for receipt in recipients:
            number = receipt
            multiple_numbers.append(number)
        add_multiple_numbers_to_url = ','.join(multiple_numbers)
        print(doc.name)
        
        try:
            # Fetch the video file
            video_file = frappe.get_all('File', filters={"attached_to_name": doc.name, "attached_to_doctype": doc.doctype}, fields=["name", "file_url"])
            if not video_file:
                frappe.throw(_("No video file found attached to the document."))
            
            video_file_doc = frappe.get_doc('File', video_file[0].name)
            site_url = frappe.utils.get_url()
            video_file_url = f"{site_url}{video_file_doc.file_url}"
            
            print(video_file_url)
            
            payload = {
                'token': token,
                'to': add_multiple_numbers_to_url,
                'body': msg1,
                "video": video_file_url,
            }
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            
            time.sleep(10)
            response = requests.post(video_url, data=payload, headers=headers)
            # When the message is successfully sent, its details are stored in ultramsg_4_ERPNext log  
            if response.status_code == 200:
                response_json = response.json()
                print(response_json)
                if "sent" in response_json and response_json["sent"] == "true":
                    # Log success
                    current_time = now()  # for getting current time
                    msg1 = frappe.render_template(self.message, context)
                    frappe.get_doc({"doctype": "ultramsg_4_ERPNext log", "title": "WhatsApp message successfully sent", "message": msg1, "to_number": doc.custom_mobile_phone, "time": current_time}).insert()
                elif "error" in response_json:
                    # Log error
                    frappe.log("WhatsApp API Error: ", response_json.get("error"))
                else:
                    # Log unexpected response
                    frappe.log("Unexpected response from WhatsApp API")
            else:
                # Log HTTP error
                frappe.log("WhatsApp API returned a non-200 status code: ", str(response.status_code))
            return response.text
        except Exception as e:
            frappe.log_error(title='Failed to send notification', message=frappe.get_traceback())

    # Call the appropriate send WhatsApp function based on conditions
    def send(self, doc):
        context = {"doc": doc, "alert": self, "comments": None}
        if doc.get("_comments"):
            context["comments"] = json.loads(doc.get("_comments"))
        if self.is_standard:
            self.load_standard_properties(context)      
        try:
            if self.channel == "whatsapp message":
                # If attach_print and print_format both are working then send PDF with message
                if self.attach_print or self.print_format:
                    frappe.enqueue(
                        self.send_whatsapp_with_pdf(doc, context),
                        queue="short",
                        timeout=200,
                        doc=doc,
                        context=context
                    )
                # If attach_video is checked, send video
                elif self.custom_attach_video:
                  print("Video is attached")
                  
                  frappe.enqueue(
                        self.send_whatsapp_with_video(doc, context),
                        queue="short",
                        timeout=200,
                        doc=doc,
                        context=context
                    )
                # Otherwise, send only the message   
                else:
                    frappe.enqueue(
                        self.send_whatsapp_without_pdf(doc, context),
                        queue="short",
                        timeout=200,
                        doc=doc,
                        context=context
                    )
        except:
            frappe.log_error(title='Failed to send notification', message=frappe.get_traceback())  
        super(ERPGulfNotification, self).send(doc) 

    def get_receiver_list(self, doc, context):
        """Return receiver list based on the doc field and role specified"""
        receiver_list = []
        for recipient in self.recipients:
            if recipient.condition:
                if not frappe.safe_eval(recipient.condition, None, context):
                    continue
            if recipient.receiver_by_document_field:
                fields = recipient.receiver_by_document_field.split(",")
                if len(fields) > 1:
                    for d in doc.get(fields[1]):
                        phone_number = d.get(fields[0])
                        receiver_list.append(phone_number)

            # For sending messages to the owner's mobile phone number
            if recipient.receiver_by_document_field == "owner":
                receiver_list += get_user_info([dict(user_name=doc.get("owner"))], "mobile_no")

            # For sending messages to the number specified in the receiver field
            elif recipient.receiver_by_document_field:
                receiver_list.append(doc.get(recipient.receiver_by_document_field))

            # For sending messages to specified role
            if recipient.receiver_by_role:
                receiver_list += get_info_based_on_role(recipient.receiver_by_role, "mobile_no")

        receiver_list = list(set(receiver_list))
        # Removing none_object from the list
        final_receiver_list = [item for item in receiver_list if item is not None]
        return final_receiver_list
