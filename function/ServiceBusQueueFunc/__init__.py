import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info('Python ServiceBus queue trigger processed message: %s', notification_id)

    # TODO: Get connection to database -> Done
    conn = psycopg2.connect("dbname=sqlserver-project3.postgres.database.azure.com user=datdd3@sqlserver-project3")
    cur = conn.cursor()

    try:
        # TODO: Get notification message and subject from database using the notification_id -> Done
        logging.info('Get notification message and subject')
        cur.execute("SELECT message, subject FROM public.notification WHERE id={};".format(notification_id))
        result = cur.fetchone()
        if result is not None:
            message = result[0]
            subject = result[1]
            logging.info('Notification message: ' + message)
            logging.info('Notification subject: ' + subject)

        # TODO: Get attendees email and name -> Done
        cur.execute("SELECT first_name, email FROM public.attendee;")
        attendees = cur.fetchall()        

        # TODO: Loop through each attendee and send an email with a personalized subject -> Done
        if attendees is not None:
            for attendee in attendees:                
                logging.info(attendee)
                name = attendee[0]
                email = attendee[1]
                subject = '{}: {}'.format(name, subject)
                send_email(email, subject, message)

        # TODO: Update the notification table by setting the completed date and updating the status with the total number of attendees notified - Done
        completed_date = datetime.utcnow()
        status = 'Notified {} attendees'.format(len(attendees))
        cur.execute("UPDATE public.notification SET status={}, completed_date={} WHERE id={};".format(status, completed_date, notification_id))

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        # TODO: Close connection
        logging.info('Close connection')
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