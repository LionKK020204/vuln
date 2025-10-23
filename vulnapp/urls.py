from django.urls import path
from . import views

urlpatterns = [
    path('', views.search, name='search'),                  # root: public search (vulnerable)
    path('echo', views.echo, name='echo'),                  # reflected XSS demo
    path('login', views.login_view, name='login'),          # admin login
    path('logout', views.logout_view, name='logout'),       # logout
    path('students/', views.student_list, name='student_list'),          # admin only
    path('students/add/', views.student_add, name='student_add'),
    path('students/edit/<int:id>/', views.student_edit, name='student_edit'),
    path('students/delete/<int:id>/', views.student_delete, name='student_delete'),
]
