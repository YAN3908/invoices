from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime
from django_bulk_update.manager import BulkUpdateManager
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


# Create your models here.


class User(AbstractUser):
    # email = models.EmailField(_("email address"), unique=True)
    phone = models.CharField(max_length=10, validators=[RegexValidator(
        regex=r'\d{10}',
        message='only digits please',
        code='invalid',
        inverse_match=False
    )])
    access_allowed = models.BooleanField(default=False)
    email_verify = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.access_allowed:
            companies = Company.objects.filter(boss=self.pk)
            for company in companies:
                company.access_allowed = True
            Company.objects.bulk_update(companies, update_fields=['access_allowed'])
        else:
            # Company.objects.bulk_update(companies)
            if not self.access_allowed:
                companies = Company.objects.filter(boss=self.pk)
                for company in companies:
                    company.access_allowed = False
                Company.objects.bulk_update(companies, update_fields=['access_allowed'])
        super().save(*args, **kwargs)


class Company(models.Model):
    company_name = models.CharField(max_length=256)
    regcode = models.IntegerField(blank=True, null=True, )
    boss = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name="boss")
    accountant = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="accountant")
    invitation = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="invitation")
    email = models.EmailField(blank=True, null=True)
    access_allowed = models.BooleanField(default=True)
    objects = BulkUpdateManager()


class Invoice(models.Model):
    file_obj = models.FileField(upload_to='media/')
    description = models.CharField(max_length=256)
    company_invoice = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sent_invoices")
    for_the_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="received_invoices")
    time_send = models.DateTimeField(default=datetime.now)
    paid = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="paid")
    remainder = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="remainder")
    mail_sent = models.BooleanField(null=True, default=None)

    def __str__(self):
        return f"{self.company_invoice} -> {self.for_the_company}"
