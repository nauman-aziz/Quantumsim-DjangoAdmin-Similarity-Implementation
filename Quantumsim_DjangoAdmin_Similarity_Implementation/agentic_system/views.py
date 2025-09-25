from django.shortcuts import render

# Create your views here.

from django.db.models import Q
import django_tables2 as tables
from .models import Tool
from .tables import ToolTable  # your django-tables2 Table definition

def tool_list_view(request):
    queryset = Tool.objects.all()
    q = request.GET.get('q', '')
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) |
            Q(signature__icontains=q) |
            Q(description__icontains=q) |
            Q(labels__icontains=q)
        )
    table = ToolTable(queryset)
    tables.RequestConfig(request, paginate={"per_page": 10}).configure(table)
    return render(request, "agentic_system/tool_list.html", {"table": table, "q": q})