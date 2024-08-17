from django.urls import path
from flashcards_app import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path("logout/",LogoutView.as_view(next_page='login'),name='logout'),
    path("",views.login_view,name='login'),
    path("register/",views.register,name='register'),
    path('home/', views.home, name='home'),
]