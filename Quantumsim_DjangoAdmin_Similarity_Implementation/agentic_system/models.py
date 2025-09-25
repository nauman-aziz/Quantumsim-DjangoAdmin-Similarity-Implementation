import uuid
from django.db import models


class Agent(models.Model):
    name = models.CharField(max_length=150, unique=False)
    available_to_users = models.BooleanField(default=True)
    system_default = models.BooleanField(default=False)
    description = models.TextField()
    agent_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # LLM choices
    LLM_CHOICES = [
        ('QS LLM Sharp Agent', 'QS LLM Sharp Agent'),
        ('QS-LLM Fast','QS-LLM Fast'),
        ('QS-LLM Sharp Base priority','QS-LLM Sharp Base priority'),
        ('QS-LLM Sharp Hi Priority','QS-LLM Sharp Hi Priority'),
        ('QS-LLM Smart','QS-LLM Smart'),
        ('QS-LLM SmartDev','QS-LLM SmartDev'),
        ('QS-LLM Smart Synovus Classification','QS-LLM Smart Synovus Classification'),
        ('QS-LLM Smart Synovus','QS-LLM Smart Synovus'),
        ('QS-LLM Sharp','QS-LLM Sharp')
        # Add other LLM choices here if they exist
    ]

    AGENT_PROMPT_TEMPLATE_CHOICES = [
        ('oracle procurement agent system prompt', 'oracle procurement agent system prompt'),
        # Add other template choices here if needed
    ]

    agent_prompt_template = models.CharField(
        max_length=255,
        choices=AGENT_PROMPT_TEMPLATE_CHOICES,
        default='oracle procurement agent system prompt',
        verbose_name="Agent Prompt Template"
    )
    llm = models.CharField(
        max_length=255,
        choices=LLM_CHOICES,
        default='QS-LLM Fast',
        verbose_name="LLM"
    )
    bypass = models.BooleanField(
        default=False,
        verbose_name="Bypass",
        help_text="Whether the original llm system prompt should be bypassed."
    )


    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"
        ordering = ["name"]

    def __str__(self):
        return self.name  


class Label(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Label"
        verbose_name_plural = "Labels"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PromptTemplate(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Prompt Template"
        verbose_name_plural = "Prompt Templates"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SecretStore(models.Model):
    name = models.CharField(max_length=150, unique=True)
    # Store arbitrary key/values; JSONField works on SQLite with Django 4.2+
    data = models.JSONField(default=dict, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Secret Store"
        verbose_name_plural = "Secret Stores"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tool(models.Model):
    name = models.CharField(max_length=150, unique=True)
    active = models.BooleanField(default=True)
    signature = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    labels = models.CharField(max_length=200)        
    associated_agents = models.CharField(max_length=150, unique=False)

    class Meta:
        verbose_name = "Tool"
        verbose_name_plural = "Tools"
        ordering = ["name"]

    def __str__(self):
        return self.name


class UtilityTool(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Utility Tool"
        verbose_name_plural = "Utility Tools"
        ordering = ["name"]

    def __str__(self):
        return self.name
