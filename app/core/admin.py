from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin 
from django.utils.translation import gettext as _

from user import models as user
from fantasy import models as fantasy
from account import models as account

class UserAdmin(BaseUserAdmin): 
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields' : ('name',)}),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser')}
        ),
        (_('Important Dates'), {'fields': ('last_login',)})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')
        }),
    )

admin.site.register(account.Account)
admin.site.register(account.PrelaunchEmail)
admin.site.register(account.Asset)
admin.site.register(account.Collection)
admin.site.register(account.SalesOrder)
admin.site.register(user.User, UserAdmin)
admin.site.register(fantasy.Position)
admin.site.register(fantasy.AthleteSeason)
admin.site.register(fantasy.StatsInfo)

@admin.register(fantasy.Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'terra_id', 'api_id')

@admin.register(fantasy.Team)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ('id', 'location', 'nickname')
