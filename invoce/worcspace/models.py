from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime
from django_bulk_update.manager import BulkUpdateManager
# Create your models here.


class User(AbstractUser):
    phone = models.CharField(max_length=10)
    blocked = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.blocked:
            companies = Company.objects.filter(boss=self.pk)
            for company in companies:
                company.blocked = True
            Company.objects.bulk_update(companies, update_fields=['blocked'])
        else:
            # Company.objects.bulk_update(companies)
            if not self.blocked:
                companies = Company.objects.filter(boss=self.pk)
                for company in companies:
                    company.blocked = False
                Company.objects.bulk_update(companies, update_fields=['blocked'])
        super().save(*args, **kwargs)


class Company(models.Model):
    company_name = models.CharField(max_length=256)
    regcode = models.IntegerField(blank=True, null=True, )
    boss = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name="boss")
    accountant = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="accountant")
    invitation = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="invitation")
    email = models.EmailField(blank=True, null=True)
    blocked = models.BooleanField(default=True)
    objects = BulkUpdateManager()

class Invoice(models.Model):
    file_obj = models.FileField(upload_to='media/')
    description = models.CharField(max_length=256)
    company_invoice = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sent_invoices")
    for_the_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="received_invoices")
    time_send = models.DateTimeField(default=datetime.now)
    paid = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="paid")
    remainder = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="remainder")

    def __str__(self):
        return f"{self.company_invoice} -> {self.for_the_company}"
