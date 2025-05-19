from django.contrib import admin
from .models import (
    Project, ProjectMember,
    Board, Sprint, Label,
    Task, Comment, ActivityLog
)

# --------------------------
# Projects and Memberships
# --------------------------

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'tenant', 'created_by', 'created_at')
    search_fields = ('name',)
    list_filter = ('tenant', 'created_at')


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role', 'joined_at')
    list_filter = ('role',)
    search_fields = ('project__name', 'user__email')


# --------------------------
# Boards, Sprints, Labels
# --------------------------

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_by', 'created_at')
    search_fields = ('name', 'project__name')
    list_filter = ('tenant', 'created_at')


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ('name', 'board', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('name', 'board__name')


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'tenant')
    search_fields = ('name',)
    list_filter = ('tenant',)


# --------------------------
# Tasks and Comments
# --------------------------

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_type', 'status', 'priority', 'board', 'assignee')
    search_fields = ('title', 'description')
    list_filter = ('status', 'task_type', 'priority', 'board', 'labels')
    autocomplete_fields = ('assignee', 'created_by', 'updated_by')

    filter_horizontal = ('labels',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'is_edited', 'created_at', 'edited_at')
    search_fields = ('content',)
    list_filter = ('is_edited',)


# --------------------------
# Activity Log
# --------------------------

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('id','actor', 'action', 'target_type', 'created_at')
    list_display_links = ('id', 'actor', 'action')
    search_fields = ('actor__email', 'action', 'target_type')
    list_filter = ('action', 'target_type', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 20
    list_select_related = ('actor', 'project')
