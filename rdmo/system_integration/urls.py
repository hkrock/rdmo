from django.urls import path
from .views import SystemsView, LoginView, ProjectView

from . import views

app_name = 'system_integration'
urlpatterns = [
        path('login/<int:rdmo_project_id>/<int:system_id>', LoginView.as_view(), name='loginform'),
        path('login/', LoginView.as_view(), name='loginform'),
        path('login/<int:rdmo_project_id>', SystemsView.as_view(), name='login'),
        path('projects/<int:rdmo_project_id>/<int:system_id>', ProjectView.as_view(), name='projects'),
        path('import/', ProjectView.as_view(), name='import'),
]
