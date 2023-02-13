import os

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
    access_allowed = models.BooleanField(default=False)
    objects = BulkUpdateManager()


# def blue_upload_to(instance, filename):
#     folder = str(instance.company_invoice.pk) + os.sep + str(instance.for_the_company.pk)
#     return 'media/' + folder + os.sep + time_send + filename

class Invoice(models.Model):
    def blue_upload_to(self, instance):
        # print('edaedawdaw', instance)
        folder = str(self.company_invoice.pk) + os.sep + str(self.for_the_company.pk)
        return 'media/' + folder + os.sep + self.time_send.strftime('%m.%d.%Y-%H.%M.%S_') + str(instance)
    file_obj = models.FileField(upload_to=blue_upload_to)
    file_name = models.CharField(max_length=256, blank=True, null=True)
    description = models.CharField(max_length=256)
    company_invoice = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sent_invoices")
    for_the_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="received_invoices")
    time_send = models.DateTimeField(default=datetime.now)
    paid = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="paid")
    remainder = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="remainder")
    email = models.EmailField(_("email address"), blank=True)
    mail_sent = models.BooleanField(null=True, default=None)

    # def __str__(self):
    #     return f"{self.company_invoice} -> {self.for_the_company}"

    # def __init__(self, *args, **kwargs):
    #     super(self.__class__, self).__init__(*args, **kwargs)
    #     self.__original_file = self.file_obj
    #     print(self.file_obj.name)
    #
    # def save(self, *args, **kwargs):
    #     self.file_name = self.file_obj.name
    #     super(self.__class__, self).save(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     print('eeeee', self.file_obj.name)
    #     self.file_name = os.path.basename(self.file_obj.name)
    #     # self.file_name = self.file_obj.name[::-1].split('_', 1)[1].replace('/aidem', '')[::-1]+'.'+self.file_obj.name[::-1].split('.')[0][::-1]
    #     super(self.__class__, self).save(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     print(self.file_obj.upload_to)
    #     self.file_obj.upload_to = f'media/{self.company_invoice}'
    #     # if self.file_obj != self.__original_file:
    #     if self.file_obj:
    #         self.file_name = self.file_obj.name
    #     else:
    #         self.file_name = ''
    # super(self.__class__, self).save(*args, **kwargs)
