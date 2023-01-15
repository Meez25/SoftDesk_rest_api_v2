"""
Tests for project APIs.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Project

from project.serializers import ProjectSerializer, ProjectDetailSerializer

PROJECTS_URL = reverse('project:project-list')


def detail_url(project_id):
    """Return project detail URL."""
    return reverse('project:project-detail', args=[project_id])


def create_project(user, **params):
    """Create and return a new project."""
    defaults = {
            'title': 'Test project',
            'description': 'Test description',
            'type': 'Test type',
            }
    defaults.update(params)
    return Project.objects.create(author_user_id=user, **defaults)


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicProjectApiTests(TestCase):
    """Test the public feature of the project API."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving projects."""
        res = self.client.get(PROJECTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateProjectApiTests(TestCase):
    """Test the private feature of the project API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
                email="user@example.com",
                password="testpass123",
                )
        self.client.force_authenticate(self.user)

    def test_retrieve_projects(self):
        """Test retrieving projects."""
        create_project(user=self.user)
        create_project(user=self.user)

        res = self.client.get(PROJECTS_URL)

        projects = Project.objects.all().order_by('-id')
        serializer = ProjectSerializer(projects, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], serializer.data)

    def test_retrieve_projects_does_not_return_description(self):
        """Test that the description is not returned in the list."""
        create_project(user=self.user)
        res = self.client.get(PROJECTS_URL)

        self.assertNotIn('description', res.data['results'][0])

    def test_get_project_detail(self):
        """Test retrieving a project detail."""
        project = create_project(user=self.user)
        url = detail_url(project.id)
        res = self.client.get(url)

        serializer = ProjectDetailSerializer(project)
        self.assertEqual(res.data, serializer.data)

    def test_create_project(self):
        """Test creating a project."""
        payload = {
                'title': 'Test project',
                'description': 'Test description',
                'type': 'Test type',
                }
        res = self.client.post(PROJECTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(id=res.data['id'])
        self.assertEqual(project.title, payload['title'])
        self.assertEqual(project.description, payload['description'])
        self.assertEqual(project.type, payload['type'])
        self.assertEqual(project.author_user_id, self.user)

    def test_full_update(self):
        """Test updating a project with PUT."""
        project = create_project(user=self.user)
        payload = {
                'title': 'Test project',
                'description': 'Test description',
                'type': 'Test type',
                }
        url = detail_url(project.id)
        self.client.put(url, payload)

        project.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(v, getattr(project, k))
        self.assertEqual(project.author_user_id, self.user)

    def test_delete_project(self):
        """Test deleting a project."""
        project = create_project(user=self.user)
        url = detail_url(project.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)

    def test_partial_update_is_impossible(self):
        """That that the patch method is not allowed."""
        project = create_project(user=self.user)
        url = detail_url(project.id)
        res = self.client.patch(url, {
            'title': 'Test project updated',
            })

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_project_by_other_user(self):
        """Test deleting a project by other user."""
        other_user = create_user(
                email="otheruser@example.com",
                password="testpass123",
                )
        project = create_project(user=other_user)
        url = detail_url(project.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Project.objects.count(), 1)
