from uuid import UUID
from django.contrib import admin
from django.db.models import Q
from .models import Agent, Label, PromptTemplate, SecretStore, Tool, UtilityTool, Persona
import csv
import yaml
from django.contrib import admin, messages
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
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
    # list_filter = ("available_to_users", "system_default")  # native filters still work
    change_list_template = "admin/agentic_system/agent/change_list.html"

    def changelist_view(self, request, extra_context=None):
        if request.GET.get("download") == "csv":
            return self.download_csv(request)
        return super().changelist_view(request, extra_context)
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "upload-config/",
                self.admin_site.admin_view(self.upload_config),
                name="agentic_system_agent_upload_config",  # this name must match template
            ),
        ]
        return my_urls + urls

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

    def upload_config(self, request):
        """
        POST endpoint to handle YAML upload and upsert Agents, Tools, Utility Tools.
        YAML shape (example):
        ---
        force_update: false
        agents:
          - name: "Researcher"
            available_to_users: true
            system_default: false
            description: "Does research"
            agent_uuid: "optional-uuid"
        tools:
          - name: "WebSearch"
            description: "Search the web"
        utility_tools:
          - name: "CsvExporter"
            description: "Exports CSV"
        """
        if request.method != "POST":
            return HttpResponseRedirect(reverse("admin:agentic_system_agent_changelist"))

        f = request.FILES.get("agent_config_file")
        if not f:
            messages.error(request, "No file was provided.")
            return HttpResponseRedirect(reverse("admin:agentic_system_agent_changelist"))

        try:
            content = f.read().decode("utf-8", errors="ignore")
            data = yaml.safe_load(content) or {}
        except Exception as e:
            messages.error(request, f"Invalid YAML: {e}")
            return HttpResponseRedirect(reverse("admin:agentic_system_agent_changelist"))

        def as_bool(v, default=False):
            if isinstance(v, bool): return v
            if v is None: return default
            return str(v).lower() in ("1", "true", "yes", "y", "on")

        global_force = as_bool(data.get("force_update"), False)

        created, updated, skipped = [], [], []

        # --- Agents ---
        for item in (data.get("agents") or []):
            name = (item.get("name") or "").strip()
            if not name:
                continue
            force = as_bool(item.get("force_update"), global_force)

            obj = Agent.objects.filter(name=name).first()
            if obj and not force:
                skipped.append(f"Agent:{name}")
                continue

            values = {
                "available_to_users": as_bool(item.get("available_to_users"), True),
                "system_default": as_bool(item.get("system_default"), False),
                "description": item.get("description") or "",
            }
            agent_uuid = item.get("agent_uuid")
            if agent_uuid:
                try:
                    values["agent_uuid"] = UUID(str(agent_uuid))
                except Exception:
                    pass

            if obj:
                for k, v in values.items():
                    setattr(obj, k, v)
                obj.save()
                updated.append(f"Agent:{name}")
            else:
                obj = Agent.objects.create(name=name, **values)
                created.append(f"Agent:{name}")

        # --- Tools ---
        for item in (data.get("tools") or []):
            name = (item.get("name") or "").strip()
            if not name:
                continue
            force = as_bool(item.get("force_update"), global_force)
            obj = Tool.objects.filter(name=name).first()
            if obj and not force:
                skipped.append(f"Tool:{name}")
                continue
            desc = item.get("description") or ""
            if obj:
                obj.description = desc
                obj.save()
                updated.append(f"Tool:{name}")
            else:
                Tool.objects.create(name=name, description=desc)
                created.append(f"Tool:{name}")

        # --- Utility Tools ---
        for item in (data.get("utility_tools") or []):
            name = (item.get("name") or "").strip()
            if not name:
                continue
            force = as_bool(item.get("force_update"), global_force)
            obj = UtilityTool.objects.filter(name=name).first()
            if obj and not force:
                skipped.append(f"UtilityTool:{name}")
                continue
            desc = item.get("description") or ""
            if obj:
                obj.description = desc
                obj.save()
                updated.append(f"UtilityTool:{name}")
            else:
                UtilityTool.objects.create(name=name, description=desc)
                created.append(f"UtilityTool:{name}")

        msg = (
            f"Created: {len(created)} | Updated: {len(updated)} | Skipped: {len(skipped)}."
        )
        if created: msg += f" Created -> {', '.join(created[:5])}{'…' if len(created)>5 else ''}"
        if updated: msg += f" Updated -> {', '.join(updated[:5])}{'…' if len(updated)>5 else ''}"
        if skipped: msg += f" Skipped -> {', '.join(skipped[:5])}{'…' if len(skipped)>5 else ''}"

        messages.success(request, f"Agent Config processed. {msg}")
        return HttpResponseRedirect(reverse("admin:agentic_system_agent_changelist"))



@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "label_uuid")
    search_fields = ("name", "description", "label_uuid")
    search_fields = ("name", "description", "agent_uuid")
    # list_filter = ("available_to_users", "system_default")  # native filters still work
    change_list_template = "admin/agentic_system/agent/change_list.html"
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Sharing Options', {
            'fields': ('available_to_all_users', 'shared_with_users', 'shared_with_groups', 'shared_with_personas')
        }),
    )
    filter_horizontal = ('shared_with_users', 'shared_with_groups', 'shared_with_personas')


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


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
