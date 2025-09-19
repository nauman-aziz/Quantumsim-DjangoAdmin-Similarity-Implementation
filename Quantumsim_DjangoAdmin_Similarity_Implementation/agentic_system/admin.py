from uuid import UUID
from django.contrib import admin
from django.db.models import Q
from .models import Agent, Label, PromptTemplate, SecretStore, Tool, UtilityTool
import csv
from django.http import HttpResponse


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "available_to_users",
        "system_default",
        "description",
        "agent_uuid",
    )
    search_fields = ("name", "description", "agent_uuid")
    list_filter = ("available_to_users", "system_default")  # native filters still work
    change_list_template = "admin/agentic_system/agent/change_list.html"

    def changelist_view(self, request, extra_context=None):
        if request.GET.get("download") == "csv":
            return self.download_csv(request)
        return super().changelist_view(request, extra_context)

    # table content export functionality 
    def download_csv(self , request , queryset=None):
        """Export Agents to CSV (with current filters)."""
        # If no queryset passed, export the whole filtered queryset
        qs = queryset if queryset is not None else self.get_queryset(request)

        response = HttpResponse(content_type ="text/csv")
        response['Content-Disposition'] = 'attachment; filename="agents.csv"'

        writer = csv.writer(response)
        #Header
        writer.writerow(["Name", "Available To Users", "System Default", "Description", "Agent UUID"])

        #Rows
        for agent in qs:
            writer.writerow([
                agent.name,
                agent.available_to_users,
                agent.system_default,
                agent.description,
                agent.agent_uuid,
            ])
            
        return response




    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Apply dynamic filters coming from the right-side form
        index = 0
        combined_q = Q()
        exclude_q = Q()

        while True:
            col_key = f"filter_column_{index}"
            act_key = f"filter_action_{index}"
            val_key = f"filter_value_{index}"

            if col_key not in request.GET and val_key not in request.GET:
                break

            column = request.GET.get(col_key, "").strip()
            action = request.GET.get(act_key, "include").strip()
            value = request.GET.get(val_key, "").strip()

            if not column:
                index += 1
                continue

            # map UI names to model fields
            field_map = {
                "name": "name",
                "available_to_users": "available_to_users",
                "system_default": "system_default",
                "description": "description",
                "agent_uuid": "agent_uuid",
            }
            field = field_map.get(column)
            if not field:
                index += 1
                continue

            def parse_bool(s: str):
                s = s.lower()
                return s in ("1", "true", "yes", "y", "on")

            # Build a Q() for the current pair
            q = Q()
            if action in ("include", "exclude", "lt", "lte", "gt", "gte"):
                if field in ("available_to_users", "system_default"):
                    # boolean field comparisons only make sense for include/exclude
                    if value != "":
                        q = Q(**{field: parse_bool(value)})
                    else:
                        # empty value means no-op
                        q = Q()
                elif field in ("name", "description"):
                    if action in ("include", "exclude"):
                        q = Q(**{f"{field}__icontains": value})
                    elif action in ("lt", "lte", "gt", "gte"):
                        # lexicographic compare on text
                        op = {"lt": "lt", "lte": "lte", "gt": "gt", "gte": "gte"}[action]
                        q = Q(**{f"{field}__{op}": value})
                elif field == "agent_uuid":
                    # Try exact UUID, otherwise icontains fallback
                    try:
                        uuid_val = UUID(value)
                        if action in ("include", "exclude"):
                            q = Q(**{field: uuid_val})
                        else:
                            # comparisons not meaningful for UUID; ignore
                            q = Q()
                    except Exception:
                        if action in ("include", "exclude"):
                            q = Q(**{f"{field}__icontains": value})
                        else:
                            q = Q()
                else:
                    q = Q()

                if action == "exclude":
                    exclude_q |= q
                else:
                    combined_q &= q if q.children else combined_q

            elif action == "is_empty":
                if field in ("name", "description"):
                    q = Q(**{f"{field}__isnull": True}) | Q(**{field: ""})
                else:
                    q = Q(**{f"{field}__isnull": True})
                combined_q &= q

            elif action == "is_not_empty":
                if field in ("name", "description"):
                    q = ~(Q(**{f"{field}__isnull": True}) | Q(**{field: ""}))
                else:
                    q = Q(**{f"{field}__isnull": False})
                combined_q &= q

            index += 1

        if combined_q.children:
            qs = qs.filter(combined_q)
        if exclude_q.children:
            qs = qs.exclude(exclude_q)
        return qs


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at", "created_at")
    search_fields = ("name", "description", "content")
    ordering = ("name",)


@admin.register(SecretStore)
class SecretStoreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "description")


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "description")


@admin.register(UtilityTool)
class UtilityToolAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "description")
