from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from accounts.middleware.current_user import get_current_user
from projects.models import Project, Board, Sprint, Task, Label, Comment, ProjectMember, ActivityLog
from accounts.models import CustomUser

# List the models you want to log
TRACKED_MODELS = [Project, Board, Sprint, Task, Label, Comment, ProjectMember]

def get_display_str(instance):
    """String for admin or audit log display."""
    for field in ['title', 'name', 'goal', 'content']:
        if hasattr(instance, field):
            return str(getattr(instance, field))[:255]
    return str(instance)[:255]

def get_actor(instance):
    """
        Always prefer the user from thread/coroutine-local storage (the current request or consumer).
        Fall back to updated_by/created_by for legacy, bulk, or management scripts.
        """
    user = get_current_user() if get_current_user() is not None and isinstance(get_current_user(), CustomUser) else None

    # fallback: for scripts/management commands/etc.
    return user or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None) or getattr(instance,
                                                                                                    'user', None)

def get_project(instance):
    """Get related project if available."""
    return getattr(instance, 'project', None)

def get_tenant(instance):
    """Get related tenant if available."""
    return getattr(instance, 'tenant', None)

def collect_field_values(instance):
    """Returns {field_name: value, ...} for all concrete fields."""
    data = {}
    for field in instance._meta.fields:
        data[field.name] = getattr(instance, field.name, None)
    return data

def get_changed_fields(old_data, new_data):
    """Return a dict of fields that changed."""
    changes = {}
    for key in new_data:
        if key not in old_data:
            continue
        if old_data[key] != new_data[key]:
            changes[key] = {"old": old_data[key], "new": new_data[key]}
    return changes

def log_activity(instance, action, changes=None):
    ActivityLog.objects.create(
        tenant=get_tenant(instance),
        project=get_project(instance),
        actor=get_actor(instance),
        action=action,
        target_content_type=ContentType.objects.get_for_model(instance),
        target_object_id=instance.pk,
        target_type=instance.__class__.__name__,
        target_repr=get_display_str(instance),
        changed_fields=changes or None,
    )

# Pre-save: store old data for update checks
for model in TRACKED_MODELS:
    @receiver(pre_save, sender=model)
    def _store_old_data(sender, instance, **kwargs):
        if instance.pk:
            try:
                old = sender.objects.get(pk=instance.pk)
                instance._old_data = collect_field_values(old)
            except sender.DoesNotExist:
                instance._old_data = {}
        else:
            instance._old_data = {}

# Post-save: log create/update
for model in TRACKED_MODELS:
    @receiver(post_save, sender=model)
    def _log_save(sender, instance, created, **kwargs):
        if created:
            log_activity(instance, "created")
        else:
            old_data = getattr(instance, "_old_data", {}) or {}
            new_data = collect_field_values(instance)
            changes = get_changed_fields(old_data, new_data)
            if changes:  # only log if something actually changed
                log_activity(instance, "updated", changes=changes)

# Post-delete: log delete
for model in TRACKED_MODELS:
    @receiver(post_delete, sender=model)
    def _log_delete(sender, instance, **kwargs):
        log_activity(instance, "deleted")