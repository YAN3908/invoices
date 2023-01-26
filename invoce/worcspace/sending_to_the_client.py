# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail, From, To
# import os

def message_registration(to_emails):
    pass
    # message = Mail(
    #     from_email=From('ubelitis390871@gmail.com', 'Exchange of invoices'),
    #     to_emails=to_emails,
    #     subject='Exchange of invoices',
    #     html_content="<strong>Welcome to the Exchange of invoices community. We're happy you've signed up for an account with us.</strong>")
    # try:
    #     sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    #     # sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    #     response = sg.send(message)
    #     print(response.status_code)
    #     print(response.body)
    #     print(response.headers)
    #
    # except Exception as e:
    #     print(e)