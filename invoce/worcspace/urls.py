from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from . import views
from .views import Register, MyLoginView, EmailVerify, InvoiceRedactor

urlpatterns = [

                  path("confirm_email/", TemplateView.as_view(template_name='registration/confirm_email.html'),
                       name="confirm_email"),
                  path("login/", MyLoginView.as_view(), name="login"),
                  path('', include('django.contrib.auth.urls')),
                  path("verify_email/<uidb64>/<token>/", EmailVerify.as_view(), name="verify_email"),
                  path("", views.index, name="index"),
                  # path("login", views.login_view, name="login"),
                  # path("logout", views.logout_view, name="logout"),
                  path("register", Register.as_view(), name="register"),
                  path("invoice/<int:invoice_id>", InvoiceRedactor.as_view(template_name='invoice_redactor.html'),
                       name="invoice_redactor"),
                  # path("register", views.register, name="register"),
                  path("new_company", views.new_company, name="new_company"),
                  path("accountant_agre", views.accountant_agre, name="accountant_agre"),
                  path("sent_company_invoices/<int:company_id>", views.sent_company_invoices,
                       name="sent_company_invoices"),
                  path("received_company_invoices/<int:company_id>", views.received_company_invoices,
                       name="received_company_invoices"),
                  path("del_accountant", views.del_accountant, name="del_accountant"),
                  # path("new_invoice/<int:company_id>", views.new_invoice, name="new_invoice"),
                  # path("new_invoice", views.new_invoice, name="new_invoice"),
                  path("profile", views.profile, name="profile"),
                  path("received_inv", views.received_inv, name="received_inv"),
                  path("sent_inv/", views.sent_inv, name="sent_inv"),
                  path("media/media/<int:pk_company>/<int:pk_for_company>/<str:file>", views.secure_file, name="secure_file"),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# urlpatterns = [
#                   path("", views.index, name="index"),
#               ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#    path("<int:company_id>", views.new_invoice, name="new_invoice"),
