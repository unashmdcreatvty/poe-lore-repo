from django.urls import path
from . import views

app_name = 'lore'

urlpatterns = [
    path('', views.home, name='home'),
    path('entries/<int:pk>/', views.entry_detail, name='entry_detail'),
    path('submit/', views.submit_entry, name='submit_entry'),
    path('tags/', views.tag_browser, name='tag_browser'),
    path('users/<int:pk>/', views.user_profile, name='user_profile'),
    path('vote/', views.cast_vote, name='cast_vote'),
    path('api/tags/', views.tags_autocomplete, name='tags_autocomplete'),
]
