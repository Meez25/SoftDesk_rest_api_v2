"""
Database models.
"""
from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
        AbstractBaseUser,
        BaseUserManager,
        PermissionsMixin,
        )


class UserManager(BaseUserManager):
    """Manager for user profiles."""

    def create_user(self, email,
                    password=None,
                    **extra_fields):
        """Create a new user profile."""
        if not email:
            raise ValueError("User must have an email address.")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)

        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    User in the system.
    """
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Project(models.Model):
    """Project model."""
    author_user_id = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=255)

    def __str__(self):
        """Return a string representation of the model."""
        return self.title

    def save(self, *args, **kwargs):
        """Create a contributor for the author."""
        super().save(*args, **kwargs)
        if Contributor.objects.filter(project_id=self.id,
                                      user_id=self.author_user_id
                                      ).count() == 0:
            Contributor.objects.create(
                    user_id=self.author_user_id,
                    project_id=self,
                    role='Owner',
                    permission='OWN',
                    )


class Contributor(models.Model):
    """Contributor model."""
    CONTRIBUTOR = "CTR"
    OWNER = "OWN"
    PERMISSION_CHOICES = [
        (CONTRIBUTOR, 'Contributor'),
        (OWNER, 'Owner'),
    ]
    project_id = models.ForeignKey(
            'Project',
            on_delete=models.SET_NULL,
            null=True,
            )
    user_id = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            )
    permission = models.CharField(max_length=255,
                                  choices=PERMISSION_CHOICES,
                                  default=CONTRIBUTOR,
                                  )
    role = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('project_id', 'user_id',)

    def __str__(self):
        """Return a string representation of the model."""
        return self.user_id.email


class Issue(models.Model):
    """Issue model."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tag = models.CharField(max_length=255, blank=True)
    project_id = models.ForeignKey(
            'Project',
            on_delete=models.CASCADE,
            )
    priority = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=255, blank=True)
    author_user_id = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            related_name='author_user_id',
            )
    assignee_user_id = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            related_name='assignee_user_id',
            )
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.title
