from django.urls import path
from . import views

app_name = 'cat_profiles'

urlpatterns = [
    path('', views.cat_list, name='list'),
    path('add/', views.add_cat, name='add'),
    path('<int:cat_id>/', views.cat_detail, name='detail'),
    path('<int:cat_id>/edit/', views.edit_cat, name='edit'),
    path('<int:cat_id>/delete/', views.delete_cat, name='delete'),
    path('<int:cat_id>/diet/', views.diet_plans, name='diet_plans'),
    path('<int:cat_id>/diet/add/', views.add_diet_plan, name='add_diet_plan'),
]