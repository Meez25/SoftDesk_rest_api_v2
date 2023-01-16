"""
Tests for project APIs.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Project, Contributor, Issue, Comment

from project.serializers import ProjectSerializer, ProjectDetailSerializer

PROJECTS_URL = reverse('project:project-list')


def detail_url(project_id):
    """Return project detail URL."""
    return reverse('project:project-detail', args=[project_id])


def users_detail_url(user_id):
    """Return user detail URL."""
    return reverse('project:users:users-detail', args=[user_id])


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


def create_issue(project, user, **params):
    """Create and return a new issue."""
    defaults = {
            'title': 'Test issue',
            'description': 'Test description',
            'tag': 'Test tag',
            'priority': 'Test priority',
            'status': 'Test status',
            }
    defaults.update(params)
    return Issue.objects.create(project_id=project,
                                author_user_id=user,
                                assignee_user_id=user,
                                **defaults)


def create_comment(issue, user, **params):
    """Create a comment."""
    defaults = {
            'description': 'Test description',
            }
    defaults.update(params)
    return Comment.objects.create(issue_id=issue,
                                  author_user_id=user,
                                  **defaults)


class PublicProjectApiTests(TestCase):
    """Test the public feature of the project API."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving projects."""
        res = self.client.get(PROJECTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_project(self):
        """Test to verify that an unauthenticated user
        cannot create a project."""
        payload = {
                'title': 'Test project',
                'description': 'Test description',
                'type': 'Test type',
                }
        res = self.client.post(PROJECTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_contributors(self):
        """Test to verify that an unauthenticated user
        cannot create a contributor."""
        payload = {
                'project_id': 1,
                'user_id': 1,
                'permission': 'CTR',
                'role': 'developer',
                }
        res = self.client.post(reverse('project:projects-users-list',
                                       args=[1]),
                               payload)

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

    def test_create_contributor(self):
        """Test creating a contributor."""
        other_user = create_user(
                email="other_user@example.com",
                password="testpass123",
                )
        project = create_project(user=self.user)
        payload = {
                'project_id': project.id,
                'user_id': other_user.id,
                'role': 'Test role',
                'permission': 'CTR',
                }
        res = self.client.post(reverse('project:projects-users-list',
                                       args=[project.id]),
                               payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        contributor = Contributor.objects.get(id=res.data['id'])
        self.assertEqual(contributor.project_id, project)
        self.assertEqual(contributor.user_id, other_user)
        self.assertEqual(contributor.role, payload['role'])
        self.assertEqual(contributor.permission, payload['permission'])

    def test_create_bad_contributor(self):
        """Test creating a bad contributor raises an error."""
        other_user = create_user(
                email="other_user@example.com",
                password="testpass123",
                )
        project = create_project(user=self.user)
        payload = {
                'project_id': project.id,
                'user_id': other_user.id,
                'role': 'Test role',
                'permission': 'bad permission',
                }
        res = self.client.post(reverse('project:projects-users-list',
                                       args=[project.id]),
                               payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Contributor.objects.count(), 1)

    def test_create_contributor_when_project_is_created(self):
        """That that the author of the project is set as a contributor."""
        project = create_project(user=self.user)
        contributor = Contributor.objects.filter(project_id=project.id,
                                                 user_id=self.user)
        self.assertTrue(contributor.exists())
        self.assertEqual(len(contributor), 1)

    def test_delete_contributor(self):
        """Test that test the deletion of a contributor."""
        other_user = create_user(
                email="other_user@example.com",
                password="testpass123",
                )
        project = create_project(user=self.user)
        contributor = Contributor.objects.create(
                project_id=project,
                user_id=other_user,
                role='Test role',
                permission='CTR',
                )
        url = reverse('project:projects-users-detail', args=[project.id,
                                                             contributor.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Contributor.objects.count(), 1)

    def test_delete_contributor_by_contributor_not_allowed(self):
        """Test that a contributor cannot delete another contributor."""
        other_user = create_user(
                email="other_user@example.com",
                password="testpass123",
                )
        project = create_project(user=self.user)
        Contributor.objects.create(
                project_id=project,
                user_id=other_user,
                role='Test role',
                permission='CTR',
                )
        owner_contributor = Contributor.objects.get(project_id=project.id,
                                                    user_id=self.user)
        url = reverse('project:projects-users-detail',
                      args=[project.id,
                            owner_contributor.id])
        other_user_client = APIClient()
        other_user_client.force_authenticate(user=other_user)
        res = other_user_client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Contributor.objects.count(), 2)

    def test_retrieve_contributors(self):
        """Test retrieving contributors."""
        other_user = create_user(
                email="hello@example.com",
                password="testpass123",
                )
        project = create_project(user=self.user)
        Contributor.objects.create(
                project_id=project,
                user_id=other_user,
                role='Test role',
                permission='CTR',
                )
        url = reverse('project:projects-users-list', args=[project.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 2)

    def test_forbid_contributor_detail(self):
        """Test that a contributor cannot access the contributor detail."""
        other_user = create_user(
                email="hello@example.com",
                password="testpass123",
                )
        project = create_project(user=self.user)
        contributor = Contributor.objects.create(
                project_id=project,
                user_id=other_user,
                role='Test role',
                permission='CTR',
                )
        url = reverse('project:projects-users-detail', args=[project.id,
                                                             contributor.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_retrieve_project_issue_list(self):
        """Test to retrieve the list of issue related to a project."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        create_issue(project=project, user=self.user)
        url = reverse('project:projects-issues-list', args=[project.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 2)
        self.assertEqual(res.data['results'][0]['id'], issue.id)

    def test_create_an_issue_in_project(self):
        """Test to create an issue in a project."""
        project = create_project(user=self.user)
        payload = {
                'title': 'Test issue',
                'description': 'Test description',
                'project_id': project.id,
                'tag': 'Test tag',
                'status': 'Test status',
                'priority': 'Test priority',
                'author_user_id': self.user.id,
                'assignee_user_id': self.user.id,
                }
        url = reverse('project:projects-issues-list', args=[project.id])
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['title'], payload['title'])
        self.assertEqual(res.data['description'], payload['description'])
        self.assertEqual(res.data['project_id'], project.id)
        self.assertEqual(res.data['tag'], payload['tag'])
        self.assertEqual(res.data['status'], payload['status'])
        self.assertEqual(res.data['priority'], payload['priority'])
        self.assertEqual(res.data['author_user_id'], self.user.id)
        self.assertEqual(res.data['assignee_user_id'], self.user.id)

    def test_create_an_issue_in_project_with_no_permission(self):
        """Test to create an issue in a project with no permission."""
        other_user = create_user(
                email="test@example.com",
                password="testpass123",
                )
        project = create_project(user=self.user)
        client2 = APIClient()
        client2.force_authenticate(user=other_user)
        payload = {
                'title': 'Test issue',
                'description': 'Test description',
                'project_id': project.id,
                'tag': 'Test tag',
                'status': 'Test status',
                'priority': 'Test priority',
                'author_user_id': self.user.id,
                'assignee_user_id': self.user.id,
                }
        url = reverse('project:projects-issues-list', args=[project.id])
        res = client2.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_an_issue(self):
        """Test that updates an issue."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        payload = {
                'title': 'Test issue',
                'description': 'Test description',
                'project_id': project.id,
                'tag': 'Test tag',
                'status': 'Test status',
                'priority': 'Test priority',
                'author_user_id': self.user.id,
                'assignee_user_id': self.user.id,
                }
        url = reverse('project:projects-issues-detail', args=[project.id,
                                                              issue.id])
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['title'], payload['title'])
        self.assertEqual(res.data['description'], payload['description'])
        self.assertEqual(res.data['project_id'], project.id)
        self.assertEqual(res.data['tag'], payload['tag'])
        self.assertEqual(res.data['status'], payload['status'])
        self.assertEqual(res.data['priority'], payload['priority'])
        self.assertEqual(res.data['author_user_id'], self.user.id)
        self.assertEqual(res.data['assignee_user_id'], self.user.id)

    def test_unauthorized_user_cannot_see_issue_list(self):
        """Test that an unauthorized user cannot see the list of issues."""
        other_user = create_user(
                email="test@example.com",
                password="testpass123",
                )
        project = create_project(user=self.user)
        client2 = APIClient()
        client2.force_authenticate(user=other_user)
        create_issue(project=project, user=self.user)
        create_issue(project=project, user=self.user)
        url = reverse('project:projects-issues-list', args=[project.id])
        res = client2.get(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_an_issue(self):
        """Test that deletes an issue."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        url = reverse('project:projects-issues-detail', args=[project.id,
                                                              issue.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Issue.objects.count(), 0)

    def test_unauthorized_user_cannot_delete_an_issue(self):
        """That that an unauthorized user cannot delete an issue."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        url = reverse('project:projects-issues-detail',
                      args=[project.id, issue.id])
        user = create_user(
                email="test@example.com",
                password="testpass123",
                )
        client2 = APIClient()
        client2.force_authenticate(user=user)
        res = client2.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_not_possible(self):
        """That that the patch method is not possible."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        url = reverse('project:projects-issues-detail',
                      args=[project.id, issue.id])
        payload = {
                'title': 'patch',
                }
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_detail_not_possible(self):
        """Test that the get of the detail view is not possible."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        url = reverse('project:projects-issues-detail',
                      args=[project.id, issue.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_comment_in_issue(self):
        """Test that creates a comment in an issue."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        url = reverse('project:projects-issues-comments-list',
                      args=[project.id, issue.id])
        payload = {
                'description': 'test description',
                'author_user_id': self.user.id,
                'issue_id': issue.id,
                }
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['description'], payload['description'])
        self.assertEqual(res.data['author_user_id'], self.user.id)
        self.assertEqual(res.data['issue_id'], issue.id)

    def test_unauthorized_user_cannot_comment_an_issue(self):
        """Test that an unauthorized user cannot post a comment on an issue."""
        other_user = create_user(
                email="other@example.com",
                password="testpass123",
                )
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        url = reverse('project:projects-issues-comments-list',
                      args=[project.id, issue.id])
        payload = {
                'description': 'test description',
                'author_user_id': self.user.id,
                'issue_id': issue.id,
                }
        other_client = APIClient()
        other_client.force_authenticate(user=other_user)
        res = other_client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_comment_list(self):
        """Test that gets the list of comments."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        create_comment(issue=issue, user=self.user)
        create_comment(issue=issue, user=self.user)
        url = reverse('project:projects-issues-comments-list',
                      args=[project.id, issue.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 2)
