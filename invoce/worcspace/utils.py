from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import datetime
import json
import urllib
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


def send_email_for_verify(request, user):
    current_site = get_current_site(request)
    context = {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': token_generator.make_token(user),

    }
    message = render_to_string(
        'registration/verify_email.html',
        context=context
    )
    email = EmailMessage(
        'Verify email',
        message,
        to=[user.email],
    )
    email.send()


def send_email_invoice(request, company, invoice_email, obj):
    try:
        current_site = get_current_site(request)
        merge_data = {
            'company': company,
            'domain': current_site.domain
        }
        html_body = render_to_string("invoice_email.html", merge_data)

        message = EmailMultiAlternatives(
           subject=f'invoice {company}',
           body="mail testing",
           to=[invoice_email]
        )
        message.attach_alternative(html_body, "text/html")
        if request.FILES:
            uploaded_file = request.FILES['file_obj']
            uploaded_file.seek(0)
            message.attach(uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
        message.send(fail_silently=False)
        obj.mail_sent = True
        obj.save()
    except:
        obj.mail_sent = False
        obj.save()



def check_company_in_api(reg_and_company):
    try:
        regcode = int(reg_and_company.split(' ')[0])
    except:
        return (False, ("not correct company registration code"))
    company_name = reg_and_company.replace(f'{regcode} ', '')
    url = f'https://data.gov.lv/dati/lv/api/3/action/datastore_search_sql?sql=SELECT%20*%20from%20%2225e80bf3-f107-4ab4-89ef-251b5b9374e9%22%20WHERE%20regcode={regcode}'

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            response_data = json.loads(response.read().decode())
            try:
                response_name = response_data['result']['records'][0]['name']
                response_regcode = response_data['result']['records'][0]['regcode']
                # print(response_regcode, response_name)
            except:
                return (False, ('invalid company code'))
            if str(regcode) == response_regcode and company_name == response_name:
                return (True, (regcode, company_name))
            else:
                return (False, ('this company does not exist'))
    except HTTPError as error:
        return (False, ('company registry database not responding: ', error.status, error.reason))
    except URLError as error:
        return (False, ('company registry database not responding: ', error.reason))
    except TimeoutError:
        return (False, ('company registry database not responding: ', 'Request timed out'))
    # return (True, (regcode, company_name))


def date_delta(year, mons=0):
    mons = int(mons)
    year = int(year)
    if mons == 0:
        first_date = datetime.date(year, 1, 1)
        last_date = datetime.date(year + 1, 1, 1)
    elif mons == 12:
        first_date = datetime.date(year, mons, 1)
        last_date = datetime.date(year + 1, 1, 1)
    else:
        first_date = datetime.date(year, mons, 1)
        last_date = datetime.date(year, mons + 1, 1)
    delta = (first_date, last_date)
    return delta