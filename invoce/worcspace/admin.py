from django.contrib import admin
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.admin import AdminSite
# Register your models here.
from .models import Invoice, Company

class MyAdminSite(AdminSite):

    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request)

        # Sort the apps alphabetically.
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

        # Sort the models alphabetically within each app.
        #for app in app_list:
        #    app['models'].sort(key=lambda x: x['name'])

        return app_list


# class UserCompany(admin.ModelAdmin):
#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         if db_field.name == "company":
#             kwargs["queryset"] = Company.objects.filter(boss=request.user)
#         return super(UserCompany, self).formfield_for_foreignkey(db_field, request, **kwargs)

# class companies(admin.ModelAdmin):
#     filter_horizontal = ("companies",)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ('username', 'phone')
class CompanyInline(admin.TabularInline):   # StackedInline
    model = Company
    fields = ('company_name', 'access_allowed')
    fk_name = 'boss'
    extra = 0
    readonly_fields = ('company_name',)


class Fields(admin.ModelAdmin):
    fields = ('username', 'first_name', 'last_name', 'phone', 'email', 'access_allowed', 'is_active','email_verify')
    list_display = ('username', 'phone', 'email', 'email_verify', 'access_allowed')
    inlines = [CompanyInline]
    save_on_top = True
    list_editable = ('access_allowed',)
    search_fields = ('username',)
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "company":
    #         kwargs["queryset"] = Company.objects.filter(boss=request.user)
    #     return super(Fields, self).formfield_for_foreignkey(db_field, request, **kwargs)
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display =('regcode', 'company_name', 'boss', 'access_allowed',)



User = get_user_model()
admin.site.register(User, Fields)
admin.site.register(Invoice)
# admin.site.register(Company)

