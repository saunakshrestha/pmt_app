from typing import Dict, List, Optional
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.http import Http404

from projects.models import Project
from accounts.models import CustomUser, Tenant


class ProjectService:
    @staticmethod
    def get_projects(tenant: Tenant) -> QuerySet[Project]:
        """
        Get all projects for a tenant
        """
        return Project.objects.filter(tenant=tenant)

    @staticmethod
    def get_project_by_id(tenant: Tenant, project_id: int) -> Project:
        """
        Get a specific project by ID for a tenant
        """
        try:
            return get_object_or_404(Project, tenant=tenant, id=project_id)
        except Http404:
            raise Http404("Project not found")

    @staticmethod
    def create_project(tenant: Tenant, user: CustomUser, data: Dict) -> Project:
        """
        Create a new project
        """
        project = Project(
            tenant=tenant,
            created_by=user,
            **data
        )
        project.save()
        return project

    @staticmethod
    def update_project(project: Project, data: Dict) -> Project:
        """
        Update an existing project
        """
        for key, value in data.items():
            setattr(project, key, value)

        project.save()
        return project

    @staticmethod
    def delete_project(project: Project) -> bool:
        """
        Delete a project
        """
        project.delete()
        return True