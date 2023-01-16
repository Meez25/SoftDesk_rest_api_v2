"""
URL mappings for the project app.
"""
from django.urls import path, include

from rest_framework_nested import routers

from project import views


router = routers.SimpleRouter()
router.register('projects', views.ProjectViewSet)

project_router = routers.NestedSimpleRouter(router,
                                            'projects',
                                            lookup='project')
project_router.register("users",
                        views.ContributorViewSet,
                        basename='projects-users')
project_router.register("issues",
                        views.IssueViewSet,
                        basename='projects-issues')

comment_router = routers.NestedSimpleRouter(project_router,
                                            r'issues',
                                            lookup='issue')
comment_router.register("comments", views.CommentViewSet,
                        basename='projects-issues-comments')


app_name = 'project'

urlpatterns = [
    path('', include(router.urls)),
    path('', include(project_router.urls)),
    path('', include(comment_router.urls)),
    ]
