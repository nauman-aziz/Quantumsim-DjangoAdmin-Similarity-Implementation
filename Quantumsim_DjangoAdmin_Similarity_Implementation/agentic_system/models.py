import uuid
from django.db import models


class Agent(models.Model):
    name = models.CharField(max_length=150, unique=True)
    available_to_users = models.BooleanField(default=True)
    system_default = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    agent_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

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
    description = models.TextField(blank=True)

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
