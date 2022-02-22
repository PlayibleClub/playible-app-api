from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext as _

from apps.users import models as user
from apps.fantasy import models as fantasy
from apps.account import models as account


class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name',)}),
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
admin.site.register(fantasy.Game)
admin.site.register(fantasy.GameSchedule)
admin.site.register(fantasy.GameAthlete)
admin.site.register(fantasy.GameAsset)
admin.site.register(fantasy.GameAthleteStat)
admin.site.register(fantasy.PackAddress)
admin.site.register(user.User, UserAdmin)


@admin.register(fantasy.Athlete)
class AthleteAdmin(admin.ModelAdmin):
    search_fields = ["api_id"]
    list_display = ('first_name', 'last_name', 'api_id', 'position')


@admin.register(fantasy.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'location', 'name')


@admin.register(fantasy.GameTeam)
class GameTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'fantasy_score')