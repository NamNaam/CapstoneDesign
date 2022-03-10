from django.urls import path
from . import views

app_name = 'conc'
urlpatterns = [
    path('', views.index, name='index'),
    path('project/', views.project, name='project'),
    path('detect/', views.detect, name='detect'),
    path('result/', views.result, name='result'),
    path('api/score/', views.ScoreAPIView.as_view(), name="score_api"),
]