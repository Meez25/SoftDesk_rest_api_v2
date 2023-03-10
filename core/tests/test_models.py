"""
Tests for models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from core import models


def create_user(email='user@example.com', password='testpass'):
    """Create a sample user."""
    return get_user_model().objects.create_user(email, password)


def create_project(author_user_id,
                   title='Test project',
                   description='Test description',
                   type='Test type'):
    """Create a sample project."""
    return models.Project.objects.create(author_user_id=author_user_id,
                                         title=title,
                                         description=description,
                                         type=type)


class ModelTest(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful."""
        email = 'test@example.com'
        password = "testpass123"
        first_name = "Test"
        last_name = "User"
        user = get_user_model().objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                )

        self.assertEqual(user.email, email)
        self.assertEqual(user.first_name, first_name)
        self.assertEqual(user.last_name, last_name)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
                ['test1@EXAMPLE.com', 'test1@example.com'],
                ['Test2@Example.com', 'Test2@example.com'],
                ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
                ['test4@example.COM', 'test4@example.com'],
                ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_new_superuser(self):
        """Test creating a new superuser."""
        user = get_user_model().objects.create_superuser(
                'test@example.com',
                'test123',
                )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_project(self):
        """Test creating a project."""
        user = create_user()
        project = models.Project.objects.create(
                author_user_id=user,
                title='Test Project',
                description="Test project description",
                type="test",
                )

        self.assertEqual(project.title, 'Test Project')
        self.assertEqual(project.description, 'Test project description')
        self.assertEqual(project.type, 'test')
        self.assertEqual(project.author_user_id, user)

    def test_create_contributor(self):
        """Test creating a contributor."""
        user = create_user()
        other_user = create_user(
                email="toto@toto.com",
                password="testpass",
                )
        project = create_project(user)
        contributor = models.Contributor.objects.create(
                project_id=project,
                user_id=other_user,
                permission='CTR',
                role='developer',
                )

        self.assertEqual(contributor.project_id, project)
        self.assertEqual(contributor.user_id, other_user)
        self.assertEqual(contributor.permission, 'CTR')
        self.assertEqual(contributor.role, 'developer')

    def test_forbid_duplicate_contributors(self):
        """Test that a contributor cannot be added twice."""
        user = create_user()
        project = create_project(user)
        with self.assertRaises(IntegrityError):
            models.Contributor.objects.create(
                    project_id=project,
                    user_id=user,
                    permission='contributor',
                    role='developer',
                    )

    def test_project_author_is_owner_contributor(self):
        """Test that the project author is
        automatically added as a contributor"""
        user = create_user()
        project = create_project(user)
        contributor = models.Contributor.objects.get(
                project_id=project,
                user_id=user,
                )
        self.assertEqual(contributor.project_id, project)
        self.assertEqual(contributor.user_id, user)
        self.assertEqual(contributor.permission, 'OWN')
        self.assertEqual(contributor.role, 'Owner')

    def test_create_issue(self):
        """That creating an issue."""
        user = create_user()
        project = create_project(user)
        issue = models.Issue.objects.create(
                project_id=project,
                author_user_id=user,
                title='Test Issue',
                description='Test issue description',
                tag='test tag',
                priority='test priority',
                status='test status',
                assignee_user_id=user,
                )

        self.assertEqual(issue.project_id, project)
        self.assertEqual(issue.author_user_id, user)
        self.assertEqual(issue.title, 'Test Issue')
        self.assertEqual(issue.description, 'Test issue description')
        self.assertEqual(issue.tag, 'test tag')
        self.assertEqual(issue.priority, 'test priority')
        self.assertEqual(issue.status, 'test status')
        self.assertEqual(issue.assignee_user_id, user)

    def test_create_comment(self):
        """Test creating a comment."""
        user = create_user()
        project = create_project(user)
        issue = models.Issue.objects.create(
                project_id=project,
                author_user_id=user,
                title='Test Issue',
                description='Test issue description',
                tag='test tag',
                priority='test priority',
                status='test status',
                assignee_user_id=user,
                )
        comment = models.Comment.objects.create(
                issue_id=issue,
                author_user_id=user,
                description='Test description',
                )

        self.assertEqual(comment.issue_id, issue)
        self.assertEqual(comment.author_user_id, user)
        self.assertEqual(comment.description, 'Test description')
