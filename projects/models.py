from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from accounts.models import CustomUser, Tenant

# Create your models here.

# --------------------------
# Permissions & Memberships
# --------------------------

class Project(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, related_name='project')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='project_member')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='project_member')
    role = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, related_name='project_member')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.project.name}"

# --------------------------
# Boards, Sprints, Labels
# --------------------------

class Board(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, related_name='board')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='board')
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_boards')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Sprint(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, related_name='sprint')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='sprint')
    board = models.ForeignKey(Board, on_delete=models.SET_NULL, null=True, related_name='sprint')
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

    def __str__(self):
        return self.name


class Label(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, related_name='label')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='labels')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7)  # e.g. #RRGGBB

    def __str__(self):
        return self.name


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

    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, related_name='task')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='tasks')
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
    assignee = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tasks')
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

    def __str__(self):
        return self.title


class Comment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, related_name='comment')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='comments')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"


# --------------------------
# Activity Logs (Optional)
# --------------------------


class ActivityLog(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    actor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=32)  # 'created', 'updated', 'deleted'
    target_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    target_object_id = models.PositiveIntegerField(null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')
    target_type = models.CharField(max_length=64)     # e.g., "Task", "Sprint"
    target_repr = models.CharField(max_length=255)    # str(instance) for display
    changed_fields = models.JSONField(null=True, blank=True)   # {field: {'old': x, 'new': y}, ...}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        user = self.actor.username if self.actor else "system"
        return f"{user} {self.action} {self.target_type} [{self.target_repr}] at {self.created_at:%Y-%m-%d %H:%M}"