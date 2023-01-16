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


app_name = 'project'

urlpatterns = [
    path('', include(router.urls)),
    path('', include(project_router.urls)),
    ]
