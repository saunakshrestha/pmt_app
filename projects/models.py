from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from accounts.models import CustomUser, Tenant

# Create your models here.

# --------------------------
# Roles & Permissions
# --------------------------

class Resource(models.Model):
    code = models.CharField(max_length=50, unique=True)  # e.g., 'task', 'comment'
    name = models.CharField(max_length=100)              # Human readable
    description = models.TextField(blank=True)

class Role(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    
class RolePermission(models.Model):
    ACTION_CHOICES = [
        ('view', 'View'),
        ('change', 'Change'),
        ('delete', 'Delete'),
        ('add', 'Add')
    ]
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    is_allowed = models.BooleanField(default=True)

    class Meta:
        unique_together = ('role', 'resource', 'action')

# --------------------------
# Permissions & Memberships
# --------------------------

class Project(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    role = models.CharField(max_length=20, choices=[
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ])
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)

# --------------------------
# Boards, Sprints, Labels
# --------------------------

class Board(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Sprint(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True)
    board = models.ForeignKey(Board, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    goal = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Label(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7)  # e.g. #RRGGBB


# --------------------------
# Tasks, Subtasks, Comments
# --------------------------

class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('blocked', 'Blocked'),
    ]
    TYPE_CHOICES = [
        ('task', 'Task'),
        ('bug', 'Bug'),
        ('story', 'Story'),
        ('epic', 'Epic'),
        ('subtask', 'Subtask'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True)
    board = models.ForeignKey(Board, on_delete=models.SET_NULL, null=True)
    sprint = models.ForeignKey(Sprint, null=True, blank=True, on_delete=models.SET_NULL)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subtasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='task')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    assignee = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    labels = models.ManyToManyField(Label, blank=True)
    story_points = models.IntegerField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, related_name='created_tasks', on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(CustomUser, related_name='updated_tasks', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)


class Comment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)


# --------------------------
# Activity Logs (Optional)
# --------------------------


class ActivityLog(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True)
    actor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)

    # Generic relation to ANY model: task, board, sprint, etc.
    target_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    target_object_id = models.PositiveIntegerField(null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    action = models.CharField(max_length=255)  # e.g., 'created', 'edited', 'assigned'
    metadata = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']