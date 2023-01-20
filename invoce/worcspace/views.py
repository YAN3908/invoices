# ~/invoices/invoce (master)$
import io
import os
from datetime import datetime, timedelta, date
import datetime
from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.forms import DateInput, TextInput, EmailInput, Select  # mast hewe
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
# Create your views here.
from django.contrib.auth import authenticate, login, logout
from .models import Invoice, Company
from django.template.loader import render_to_string  ################

from django.urls import reverse
from django.db import IntegrityError
from django.forms import ModelForm
from .models import User
from django.db.models import Q
import json
import urllib
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


class InvoiceForm(ModelForm):
    class Meta:
        model = Invoice
        fields = ['description', 'file_obj', ]
        labels = {
            "description": "",
            "file_obj": ""
        }
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'description'}),
            'file_obj': forms.FileInput(attrs={'id': 'inputGroupFile04'}),
            # 'image': forms.ClearableFileInput(attrs={'multiple': True})
        }
    # def __init__(self, *args, **kwargs): <input type="file" class="form-control" id="inputGroupFile04" aria-describedby="inputGroupFileAddon04" aria-label="Upload">
    #     # super(InvoiceForm, self).__init__(*args, **kwargs)
    #     if 'user' in kwargs and kwargs['user'] is not None:
    #         user = kwargs.pop('user')
    #         qs = User.objects.exclude(id=user.id)
    #
    #         # вызываем конструктор формы и добавляет query set
    #         super(InvoiceForm, self).__init__(*args, **kwargs)
    #         try:
    #             self.fields['user_sent_inv'].queryset = qs
    #         except NameError:
    #             pass


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


def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("received_inv"))
        # company = Company.objects.filter(Q(boss=request.user.id) | Q(accountant=request.user.id)).first()
        # invoices = Invoice.objects.filter(Q(company_invoice=company) | Q(for_the_company=company)).order_by('-time_send')
        # # invoices = Invoice.objects.all()
        # return render(request, "worcspace/index.html", {'invoices': invoices})
    else:
        return render(request, "worcspace/index.html",
                      {'some_text': "view that an unregistered user should see", 'link': 'sent'})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "worcspace/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "worcspace/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        phone = request.POST["phone"]
        # company_name = request.POST['company_name']
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        # if company_name == '':
        #     return render(request, "worcspace/register.html", {
        #         "message": "you must enter company name."
        #     })
        if password != confirmation:
            return render(request, "worcspace/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password, phone=phone)
            user.save()
        except IntegrityError:
            return render(request, "worcspace/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        # print(user.id)
        # company = Company(company_name=company_name, boss=user)
        # company.save()
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "worcspace/register.html")


def new_invoice(request, company_id):
    user = request.user
    company = Company.objects.filter(pk=int(company_id)).first()
    # print(company.boss, user)
    if company.boss == user or company.accountant == user:
        # if company.boss == request.user or company.accountant == request.user:
        if request.method == "POST":
            regcode_and_company = check_company_in_api(request.POST['for_the_company'])
            if regcode_and_company[0]:
                regcode = regcode_and_company[1][0]
                company_name = regcode_and_company[1][1]
                for_the_company = Company.objects.filter(pk=regcode).first()
                if for_the_company:
                    for_the_company.company_name = company_name
                    for_the_company.save(update_fields=["company_name"])
                else:
                    for_the_company = Company.objects.create(pk=regcode, company_name=company_name, regcode=regcode, )
                    for_the_company.save()
                form = InvoiceForm(request.POST, request.FILES)
                if for_the_company.pk == int(company.pk):
                    return render(request, "worcspace/sent_company_invoices.html",
                                  {'form': form, 'company': company, "message": "you send yourself"})
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.company_invoice = company
                    obj.for_the_company = for_the_company
                    obj.save()
                    form.save_m2m()
                    return HttpResponseRedirect(reverse("sent_company_invoices", args=(company_id,)))
                else:
                    return render(request, "worcspace/sent_company_invoices.html",
                                  {'form': form, 'company': company, "message": "invalid data"})
            else:
                return HttpResponse(regcode_and_company[1])
                # return HttpResponse(
                #     "<p style='color: red'>Сompany does not exist</p> ")  # <button onclick="history.back()">Go Back</button>
        else:
            # forma = InvoiceForm(user=request.user)
            return HttpResponseRedirect(reverse("index"))
    else:
        return HttpResponse("you do not have access!")


@login_required(login_url="index")
def sent_inv(request):
    if request.method == "POST":
        path = request.POST.get("path")
        for pk_invoice in request.POST:
            if pk_invoice.isdigit():
                invoice = Invoice.objects.filter(pk=pk_invoice).first()
                if invoice.company_invoice.boss == request.user or invoice.company_invoice.accountant == request.user:
                    if request.POST.get(pk_invoice) == 'Paid':
                        # print(request.POST.get(pk_invoice))

                        invoice.paid = request.user
                        invoice.save()
                    elif request.POST.get(pk_invoice) == 'Remainder':
                        # print(request.POST.get(pk_invoice))

                        invoice.remainder = request.user
                        invoice.save()
                    elif request.POST.get(pk_invoice) == 'Reset':
                        # print(request.POST.get(pk_invoice))

                        invoice.remainder = None
                        invoice.paid = None
                        invoice.save()
                else:
                    return HttpResponseRedirect(reverse("index"))
        return HttpResponseRedirect(reverse("sent_inv") + path)
    else:
        companies = Company.objects.filter(Q(boss=request.user.id) | Q(accountant=request.user.id))
        invoices = Invoice.objects.filter(company_invoice__in=companies).order_by('paid', '-remainder', '-time_send')
        # print(request.GET.get("year"))
        if request.GET.get("year"):
            # print(int(date[:4]))
            # print(int(date[5:7]))
            year = request.GET.get("year")
            mons = request.GET.get("mons")
            # print(request.GET.get("year"))
            # print(year, mons)
            invoices = invoices.filter(time_send__range=date_delta(year, mons))
            # invoices = invoices.filter(paid=None).order_by('-time_send')
        if request.GET.get("company"):
            # print(request.GET.get("company"))
            invoices = invoices.filter(for_the_company__company_name=request.GET.get("company"))
            # invoices = invoices.filter(paid=None).order_by('-time_send')
        return render(request, "worcspace/sent_inv.html",
                      {'invoices': invoices, 'link': 'sent', 'companies': companies})


@login_required(login_url="index")
def received_inv(request):
    # print(request.user.boss.first())
    companies = Company.objects.filter(Q(boss=request.user.id) | Q(accountant=request.user.id))
    invoices = Invoice.objects.filter(for_the_company__in=companies).order_by('paid', '-remainder', '-time_send')
    if request.GET.get("year"):
        # print(int(date[:4]))
        # print(int(date[5:7]))
        year = request.GET.get("year")
        mons = request.GET.get("mons")
        # print(request.GET.get("year"))
        # print(year, mons)
        invoices = invoices.filter(time_send__range=date_delta(year, mons))
        # invoices = invoices.filter(paid=None).order_by('-time_send')
    if request.GET.get("company"):
        # print(request.GET.get("company"))
        invoices = invoices.filter(company_invoice__company_name=request.GET.get("company"))
        # invoices = invoices.filter(paid=None).order_by('-time_send')
    # invoices = Invoice.objects.all()
    return render(request, "worcspace/received_inv.html", {'invoices': invoices, 'companies': companies})


# def category_create(request):
#     if not request.user.is_authenticated:
#         raise Exception('AUTH PLEASE')
#
#     form = CategoryCreateForm()
#     if request.method == "POST":
#         form = CategoryCreateForm(request.POST)
#         if form.is_valid():
#             obj = form.save(commit=False)
#             obj.user = request.user
#             obj.save()
#             form.save_m2m()
#             return redirect("category_list")
#     context = {'form':form}
#     return render(request, 'todolist/category_create.html', context)

@login_required(login_url="index")
def profile(request):
    # person=User.objects.get(pk=request.user.pk)
    # print(person.boss.all())
    if request.method == "POST":
        # print(request.POST['phone'])
        phone = request.POST['phone']
        accountant = User.objects.filter(phone=phone).first()
        if accountant:
            company_id = request.POST['company']
            company = Company.objects.filter(id=company_id).first()
            if company.boss == request.user:
                company.invitation = User.objects.get(pk=accountant.id)
                company.save()
                request.session["ph_ac"] = phone
                return HttpResponseRedirect(
                    reverse("profile"))  # HttpResponseRedirect(request.path + f"#scrol{company_id}")
            else:
                return HttpResponse("you do not have access")
        else:
            return HttpResponse("No such user exists")

    else:
        companies = Company.objects.filter(Q(boss=request.user.id) | Q(accountant=request.user.id))
        invitations = Company.objects.filter(invitation=request.user.id)
        return render(request, "worcspace/profile.html",
                      {'invitations': invitations, 'companies': companies})


def del_accountant(request):
    if request.method == "POST":
        company_id = request.POST['company']
        company = Company.objects.filter(id=company_id).first()
        if company.boss == request.user:
            company.invitation = None
            company.accountant = None
            company.save()
            return HttpResponseRedirect(reverse("profile"))
        else:
            return HttpResponse("you do not have access")
    else:
        return HttpResponse("No such pass exists")


def new_company(request):
    if request.method == "POST":
        boss = request.user
        regcode_and_company = check_company_in_api(request.POST['company'])
        if regcode_and_company[0]:
            regcode = regcode_and_company[1][0]
            company_name = regcode_and_company[1][1]
            company_in_db = Company.objects.filter(pk=regcode).first()
            if company_in_db:
                if company_in_db.boss:
                    return HttpResponse("this company is already taken")
                else:
                    company_in_db.boss = boss
                    company_in_db.save()
            else:
                # print(regcode)
                # print(company_name)
                company = Company.objects.create(pk=regcode, company_name=company_name, regcode=regcode, boss=boss)
                company.save()
        else:
            return HttpResponse(regcode_and_company[1])
    return HttpResponseRedirect(reverse("profile"))


# def add_accountant(request):
#     if request.method == "POST":
#         print(request.POST)
#         # print(request.POST['phone'])
#         phone = request.POST['phone']
#         accountant = User.objects.filter(phone=phone).first()
#         if accountant:
#
#             company_id = request.POST['company']
#
#             company = Company.objects.filter(id=company_id).first()
#             if company.boss == request.user:
#                 company.invitation = User.objects.get(pk=accountant.id)
#                 company.save()
#             else:
#                 return HttpResponse("you do not have access")
#         else:
#             return HttpResponse("No such user exists")
#     request.session["ph_ac"] = phone
#     return HttpResponseRedirect(reverse("profile"))


def accountant_agre(request):
    if request.method == "POST":
        print(request.POST)
        for invitation in request.POST:
            if invitation.isdigit():
                print(request.POST[invitation])
                company = Company.objects.filter(pk=invitation).first()
                if request.POST[invitation] == 'True':
                    print(request.POST[invitation])
                    company.accountant = request.user
                company.invitation = None
                company.save()
                # print(companies)
        # print(request.POST['phone'])
    return HttpResponseRedirect(reverse("profile"))


# form = CompanyForm(request.POST)
# if form.is_valid():
#     obj = form.save(commit=False)
#     obj.boss = request.user
#     obj.save()
#     form.save_m2m()
#     return HttpResponseRedirect(reverse("profile"))
@login_required(login_url="index")
def sent_company_invoices(request, company_id):
    if request.method == "POST":
        path = request.POST.get("path")
        for pk_invoice in request.POST:
            if pk_invoice.isdigit():
                invoice = Invoice.objects.filter(pk=pk_invoice).first()
                if invoice.company_invoice.boss == request.user or invoice.company_invoice.accountant == request.user:
                    if request.POST.get(pk_invoice) == 'Paid':
                        # print(request.POST.get(pk_invoice))

                        invoice.paid = request.user
                        invoice.save()
                    elif request.POST.get(pk_invoice) == 'Remainder':
                        # print(request.POST.get(pk_invoice))

                        invoice.remainder = request.user
                        invoice.save()
                    elif request.POST.get(pk_invoice) == 'Reset':
                        # print(request.POST.get(pk_invoice))

                        invoice.remainder = None
                        invoice.paid = None
                        invoice.save()
                else:
                    return HttpResponseRedirect(reverse("index"))
        return HttpResponseRedirect(reverse("sent_company_invoices", args=(company_id,)) + path)
        # return HttpResponseRedirect(reverse(
        #     "sent_inv") + f'?mons={request.GET.get("mons")}&year={request.GET.get("year")}&company={request.GET.get("company")}')
    else:
        companies = Company.objects.filter(Q(boss=request.user.id) | Q(accountant=request.user.id))
        try:
            company = companies.get(pk=int(company_id))
        except IntegrityError:
            return HttpResponse("you do not have access")
        invoices = Invoice.objects.filter(company_invoice=company).order_by('paid', '-remainder', '-time_send')
        # print(request.GET.get("year"))
        if request.GET.get("year"):
            # print(int(date[:4]))
            # print(int(date[5:7]))
            year = request.GET.get("year")
            mons = request.GET.get("mons")
            print(request.GET.get("year"))
            print(year, mons)
            invoices = invoices.filter(time_send__range=date_delta(year, mons))
            # invoices = invoices.filter(paid=None).order_by('-time_send')
        if request.GET.get("company"):
            print(request.GET.get("company"))
            invoices = invoices.filter(for_the_company__company_name=request.GET.get("company"))
            # invoices = invoices.filter(paid=None).order_by('-time_send')
        return render(request, "worcspace/sent_company_invoices.html",
                      {'form': InvoiceForm, 'invoices': invoices, 'company': company})
    # company = Company.objects.filter(pk=int(company_id)).first()
    # invoices = Invoice.objects.filter(company_invoice=company).order_by('-time_send')
    # return render(request, "worcspace/sent_company_invoices.html", {'invoices': invoices, 'company': company})


@login_required(login_url="index")
def received_company_invoices(request, company_id):
    companies = Company.objects.filter(Q(boss=request.user.id) | Q(accountant=request.user.id))
    try:
        company = companies.get(pk=int(company_id))
    except IntegrityError:
        return HttpResponse("you do not have access")
    invoices = Invoice.objects.filter(for_the_company=company).order_by('paid', '-remainder', '-time_send')
    if request.GET.get("year"):
        # print(int(date[:4]))
        # print(int(date[5:7]))
        year = request.GET.get("year")
        mons = request.GET.get("mons")
        print(request.GET.get("year"))
        print(year, mons)
        invoices = invoices.filter(time_send__range=date_delta(year, mons))
        # invoices = invoices.filter(paid=None).order_by('-time_send')
    if request.GET.get("company"):
        print(request.GET.get("company"))
        invoices = invoices.filter(company_invoice__company_name=request.GET.get("company"))
        # invoices = invoices.filter(paid=None).order_by('-time_send')
    return render(request, "worcspace/received_company_invoices.html",
                  {'form': InvoiceForm, 'invoices': invoices, 'company': company})


@login_required(login_url="index")
def secure_file(request, file):
    # print('wefwefwefwefaefaefrawerfawefawefaefae')
    document = get_object_or_404(Invoice, file_obj='media/' + file)
    # path, file_name = os.path.split(file)
    # print(document)
    return FileResponse(document.file_obj)
