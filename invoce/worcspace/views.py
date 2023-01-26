# ~/invoices/invoce (master)$
# import io
# import os

# import datetime
import threading

from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
# from django.forms import DateInput, TextInput, EmailInput, Select  # mast hewe
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
# Create your views here.
from django.contrib.auth import authenticate, login, logout, get_user_model
from .forms import MyUserCreationForm, MyAuthenticationForm
from .models import Invoice, Company, User
# from django.template.loader import render_to_string  ################
from django.views import View
from django.urls import reverse
from django.db import IntegrityError
from django.forms import ModelForm
from django.db.models import Q
# from .sending_to_the_client import message_registration
from django.contrib.auth.views import LoginView
from .utils import send_email_for_verify, check_company_in_api, date_delta, send_email_invoice
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator as token_generator


class EmailVerify(View):
    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)
        if user is not None and token_generator.check_token(user, token):
            user.email_verify = True
            user.save()
            login(request, user)
            return redirect('index')
        return render(request, "worcspace/index.html",
                      {'some_text': "Your link is not valid"})

    @staticmethod
    def get_user(uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (
                TypeError,
                ValueError,
                OverflowError,
                User.DoesNotExist,
                ValidationError,
        ):
            user = None
        return user


class MyLoginView(LoginView):
    form_class = MyAuthenticationForm


class Register(View):
    template_name = 'registration/register.html'

    def get(self, request):
        context = {
            'form': MyUserCreationForm
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            send_email_for_verify(request, user)
            return redirect('confirm_email')

            # login(request, user)
            # return redirect('index')
        context = {
            'form': form
        }
        return render(request, self.template_name, context=context)


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


def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("profile"))
    else:
        return render(request, "worcspace/index.html",
                      {'some_text': "view that an unregistered user should see"})


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
                    t1 = threading.Thread(target=send_email_invoice, args=(request, company.company_name, 'yan3908@ukr.net', obj))
                    t1.start()
                    # send_email_invoice(request, company.company_name, 'yan3908@ukr.net')

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


@login_required(login_url="index")
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


@login_required(login_url="index")
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
    document = get_object_or_404(Invoice, file_obj='media/' + file)
    # path, file_name = os.path.split(file)
    # print(document)
    return FileResponse(document.file_obj)
