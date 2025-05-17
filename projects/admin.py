from django.contrib import admin
from .models import (
    Resource, Role, RolePermission,
    Project, ProjectMember,
    Board, Sprint, Label,
    Task, Comment, ActivityLog
)

# --------------------------
# Permissions and Roles
# --------------------------

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'description')
    search_fields = ('name',)
    list_filter = ('tenant',)
    inlines = [RolePermissionInline]


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'resource', 'action', 'is_allowed')
    list_filter = ('action', 'is_allowed', 'resource')
    search_fields = ('role__name', 'resource__name')


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
    raw_id_fields = ('labels',)


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
    list_display = ('actor', 'target', 'action', 'created_at')
    search_fields = ('action', 'metadata')
    list_filter = ('created_at', 'actor')