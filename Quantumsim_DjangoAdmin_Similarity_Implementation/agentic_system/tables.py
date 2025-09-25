import django_tables2 as tables
from .models import Tool

class ToolTable(tables.Table):
    select = tables.CheckBoxColumn(accessor='pk', orderable=False)
    class Meta:
        model = Tool
        template_name = "django_tables2/bootstrap.html"  # Or any other template you want
        fields = ("select","name", "active", "signature", "description", "labels","associated_agents")  # Columns to show
        sequence = ("select", "name", "active", "signature", "description", "labels", "associated_agents")