from django.contrib import admin
from .models import Agent, Contact


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "last_contact", "created_at")
    list_filter = ("industry",)
    search_fields = ("name", "note")
    inlines = [ContactInline]
