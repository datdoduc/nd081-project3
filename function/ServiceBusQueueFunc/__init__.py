import logging
import azure.functions as func
import psycopg2
import os
import json
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def main(msg: func.ServiceBusMessage):
    try:
        notification_id = int(msg.get_body().decode('utf-8'))
        logging.info('Python ServiceBus queue trigger processed message: %d', notification_id)

        # TODO: Get connection to database -> Done
        conn_string = os.environ['SQLSERVER_CONNECTION_STR']
        conn = psycopg2.connect(conn_string)
        logging.info("SQL server connection established")
        cur = conn.cursor()
        
        # TODO: Get notification message and subject from database using the notification_id -> Done
        logging.info('Get notification message and subject')
        cur.execute("SELECT subject, message FROM public.notification WHERE id=%s;", (notification_id,))
        result = cur.fetchone()
        if result is not None:
            # logging.info(result)
            subject = result[0]
            message = result[1]
            logging.info('Notification subject: ' + subject)
            logging.info('Notification message: ' + message)

        # TODO: Get attendees email and name -> Done
        cur.execute("SELECT first_name, email FROM public.attendee;")
        attendees = cur.fetchall()        

        # TODO: Loop through each attendee and send an email with a personalized subject -> Done
        logging.info("Loop through each attendee and send an email")
        if attendees is not None:
            # logging.info(attendees)
            for attendee in attendees:
                logging.info(attendee)
                name = attendee[0]
                email = attendee[1]
                subject_mail = f'{name}: {subject}'
                send_email(email, subject_mail, message)

        # TODO: Update the notification table by setting the completed date and updating the status with the total number of attendees notified -> Done
        completed_date = datetime.utcnow()
        status = f'Notified {len(attendees)} attendees'
        logging.info('Update completed_date: %s, and status: %s', str(completed_date), status)
        cur.execute("UPDATE public.notification SET status=%s, completed_date=%s WHERE id=%s;", (status, completed_date, notification_id))
        conn.commit()
        logging.info('Finished updating DB')
        
        # logging.info('Finished updating DB, check data: ')
        # cur.execute("SELECT * FROM public.notification WHERE id=%s;", (notification_id,))
        # result = cur.fetchone()
        # logging.info(result)

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        # TODO: Close connection -> Done
        logging.info('Close server connection')
        cur.close()
        conn.close()


def send_email(email, subject, body):
    sendgrid_api = os.environ.get('SENDGRID_API_KEY', 'None')
    if sendgrid_api is not 'None':
        message = Mail(
            from_email='datdoduc@outlook.com',
            to_emails=email,
            subject=subject,
            plain_text_content=body)

        sg = SendGridAPIClient(sendgrid_api)
        sg.send(message)
        logging.info("Email sent to " + email)