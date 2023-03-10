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


def create_contributor(user, project):
    """Create a contributor in the project."""
    return Contributor.objects.create(
                user_id=user,
                project_id=project,
                role='Test role',
                permission='CTR',
                )


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

    def test_get_project_with_bad_id(self):
        """Test that getting a project with a bad id returns an error."""
        url = detail_url(100)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_project(self):
        """Test creating a project."""
        payload = {
                'title': 'Test project',
                'description': 'Test description',
                'type': 'front',
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
        self.assertFalse(Project.objects.exists())

    def test_delete_project_with_bad_id(self):
        """Test that should return a 404."""
        url = detail_url(100)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

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

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Project.objects.count(), 1)

    def test_a_new_user_cannot_see_any_project(self):
        """Test that a new user cannot see any project."""
        other_user = create_user(
                email="otheruser@example.com",
                password="testpass123",
                )
        other_client = APIClient()
        other_client.force_login(other_user)
        project = create_project(user=self.user)
        res = other_client.get(PROJECTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], [])
        self.assertNotIn(project, res.data['results'])

    def test_a_new_user_cannot_see_a_particular_project(self):
        """Test that a new user cannot see a project detail."""
        other_user = create_user(
                email="otheruser@example.com",
                password="testpass123",
                )
        other_client = APIClient()
        other_client.force_login(other_user)
        project = create_project(user=self.user)
        url = detail_url(project.id)
        res = other_client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

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

    def test_create_bad_contributor_with_bad_project_id(self):
        """Test creating a bad contributor raises an error."""
        other_user = create_user(
                email="other_user@example.com",
                password="testpass123",
                )
        payload = {
                'user_id': other_user.id,
                'role': 'Test role',
                'permission': 'CTR',
                }
        res = self.client.post(reverse('project:projects-users-list',
                                       args=[200]),
                               payload)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Contributor.objects.exists())

    def test_create_bad_contributor_with_bad_user_id(self):
        """Test creating a bad contributor raises an error."""
        project = create_project(user=self.user)
        payload = {
                'user_id': 200,
                'role': 'Test role',
                'permission': 'CTR',
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

    def test_a_contributor_cannot_delete_a_project(self):
        """Test that a simple contributor cannot delete a project's he's in."""
        project = create_project(user=self.user)
        other_user = create_user(
                email="other@example.com",
                password="testpass123",
                )
        create_contributor(other_user, project)
        client2 = APIClient()
        client2.force_authenticate(user=other_user)
        url = detail_url(project.id)
        res = client2.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

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

    def test_delete_unexisting_contributor_returns_an_error(self):
        """That that return an unexisting contributor returns an error."""
        project = create_project(user=self.user)
        url = reverse('project:projects-users-detail', args=[project.id, 100])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_a_contributor_in_an_unexisting_project_return_404(self):
        """That that return an unexisting contributor returns an error."""
        url = reverse('project:projects-users-detail', args=[100, 100])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

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

    def test_filter_on_contributor_s_project(self):
        """Test that only the contributor of the projects are displayed."""
        project = create_project(user=self.user)
        other_user = create_user(
                email="other_user@example.com",
                password="testpass123",
                )
        create_project(user=other_user)
        url = reverse('project:projects-users-list', args=[project.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)

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
                'tag': 'bug',
                'status': 'finished',
                'priority': 'high',
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

    def test_create_an_issue_in_a_unexisting_project(self):
        """Test to create an issue in a project."""
        payload = {
                'title': 'Test issue',
                'description': 'Test description',
                'tag': 'bug',
                'status': 'finished',
                'priority': 'high',
                'assignee_user_id': self.user.id,
                }
        url = reverse('project:projects-issues-list', args=[100])
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_issue_with_wrong_tag(self):
        """Test that creates an issue with wrong tag should return an
        error."""
        project = create_project(user=self.user)
        payload = {
                'title': 'Test issue',
                'description': 'Test description',
                'tag': 'wrong',
                'status': 'finished',
                'priority': 'high',
                'assignee_user_id': self.user.id,
                }
        url = reverse('project:projects-issues-list', args=[project.id])
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_issue_with_wrong_status(self):
        """Test that creates an issue with wrong status should return an
        error."""
        project = create_project(user=self.user)
        payload = {
                'title': 'Test issue',
                'description': 'Test description',
                'tag': 'bug',
                'status': 'wrong',
                'priority': 'high',
                'assignee_user_id': self.user.id,
                }
        url = reverse('project:projects-issues-list', args=[project.id])
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_issue_with_wrong_priority(self):
        """Test that creates an issue with wrong priority should return an
        error."""
        project = create_project(user=self.user)
        payload = {
                'title': 'Test issue',
                'description': 'Test description',
                'tag': 'bug',
                'status': 'finished',
                'priority': 'wrong',
                'assignee_user_id': self.user.id,
                }
        url = reverse('project:projects-issues-list', args=[project.id])
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_issue_of_the_project(self):
        """That that only the issue of the projects are displayed."""
        project = create_project(user=self.user)
        other_user = create_user(
                email="other_user",
                password="test123",
                )
        other_project = create_project(user=other_user)
        create_issue(project=project, user=self.user)
        create_issue(project=other_project, user=other_user)
        url = reverse('project:projects-issues-list', args=[project.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)

    def test_404_when_deleting_an_issue_that_doesnt_exist(self):
        """That that a 404 is raised when a bad issue id is used."""
        project = create_project(user=self.user)
        url = reverse('project:projects-issues-detail', args=[project.id,
                                                              100])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_an_issue_in_project_without_assignee(self):
        """Test to create an issue in a project without an
        explicit assignee."""
        project = create_project(user=self.user)
        payload = {
                'title': 'Test issue',
                'description': 'Test description',
                'tag': 'bug',
                'status': 'finished',
                'priority': 'high',
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
                'tag': 'Test tag',
                'status': 'Test status',
                'priority': 'Test priority',
                'assignee_user_id': self.user.id,
                }
        url = reverse('project:projects-issues-list', args=[project.id])
        res = client2.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_see_issue_in_a_project_without_being_contributor(self):
        """Test that a user that is not a contributor cannot see
        issues in the project."""
        project = create_project(user=self.user)
        other_user = create_user(
                email="test@example.com",
                password="testpass123",
                )
        url = reverse('project:projects-issues-list', args=[project.id])
        client2 = APIClient()
        client2.force_authenticate(user=other_user)
        res = client2.get(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_an_issue(self):
        """Test that updates an issue."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        payload = {
                'title': 'Test issue',
                'description': 'Test description',
                'tag': 'improvement',
                'status': 'in progress',
                'priority': 'low',
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
        self.assertFalse(Issue.objects.exists())

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

    def test_only_issue_author_can_modify_it(self):
        """Test that only the author is an issue can modify it."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        other_user = create_user(
                email="test@example.com",
                password="testpass123",
                )
        client2 = APIClient()
        client2.force_authenticate(user=other_user)
        payload = {
                'title': 'Test issue',
                'description': 'Test description',
                'tag': 'Test tag',
                'status': 'Test status',
                'priority': 'Test priority',
                'assignee_user_id': self.user.id,
                }
        url = reverse('project:projects-issues-detail', args=[project.id,
                                                              issue.id])
        res = client2.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_issue_author_can_delete_it(self):
        """Test that only the author is an issue can modify it."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        other_user = create_user(
                email="test@example.com",
                password="testpass123",
                )
        client2 = APIClient()
        client2.force_authenticate(user=other_user)
        url = reverse('project:projects-issues-detail', args=[project.id,
                                                              issue.id])
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
                'issue_id': issue.id,
                }
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['description'], payload['description'])
        self.assertEqual(res.data['author_user_id'], self.user.id)
        self.assertEqual(res.data['issue_id'], issue.id)

    def test_check_if_only_the_comments_of_the_issue_are_returned(self):
        """Test that checks that only the comments of the issue are
        returned."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        project2 = create_project(user=self.user)
        other_user = create_user(
                email="other_user@example.com",
                password="testpass123",
                )
        project3 = create_project(user=other_user)
        issue2 = create_issue(project=project2, user=self.user)
        issue3 = create_issue(project=project3, user=other_user)
        create_comment(issue=issue, user=self.user)
        create_comment(issue=issue2, user=self.user)
        create_comment(issue=issue3, user=other_user)
        url = reverse('project:projects-issues-comments-list',
                      args=[project.id, issue.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)

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

    def test_modify_a_comment(self):
        """That that modifies a comment."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        comment = create_comment(issue=issue, user=self.user)
        url = reverse('project:projects-issues-comments-detail',
                      args=[project.id, issue.id, comment.id])
        payload = {
                'description': 'updated description',
                }
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['description'], payload['description'])

    def test_a_contributor_cannot_delete_another_s_contributor_comment(self):
        """That that a contributor can't delete another's contributor
        comment."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        other_user = create_user(
                email="other_user@example.com",
                password="testpass123",
                )
        other_comment = create_comment(issue=issue, user=other_user)
        url = reverse('project:projects-issues-comments-detail',
                      args=[project.id, issue.id, other_comment.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_comment_detail(self):
        """Test that it is possible to get the comment detail."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        comment = create_comment(issue=issue, user=self.user)
        url = reverse('project:projects-issues-comments-detail',
                      args=[project.id, issue.id, comment.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['description'], comment.description)

    def test_get_comment_detail_that_doesnt_exist_raise_404(self):
        """Test that return 404 when a comment doesn't exist."""
        project = create_project(user=self.user)
        issue = create_issue(project=project, user=self.user)
        url = reverse('project:projects-issues-comments-detail',
                      args=[project.id, issue.id, 100])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
