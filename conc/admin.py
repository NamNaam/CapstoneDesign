from django.contrib import admin
from .models import TempScore

class TempScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'time')

admin.site.register(TempScore, TempScoreAdmin)
