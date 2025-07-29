from django.urls import path
from . import views
from .views import (
    profile_view, change_password_ajax, review_view, delete_review,
    upload_profile_photo, delete_profile_photo, get_review, create_account, 
    CustomPasswordChangeView
)

urlpatterns = [
    path('', views.index, name='home'),
    path('browse/', views.browse, name='browse'),
    path('login/', views.login, name='login'),
    path('create/', create_account, name='create'),
    path('redirect/', views.nologin, name='redirect'),
    path('rackets/all/', views.all_rackets, name='all_rackets'),
    path('browse/<str:name>/', views.brand_page, name='brand_page'),
    path('browse/<str:name>/<slug:slug>/', views.racket_detail, name='racket_detail'),
    path('racket/<slug:slug>/review/', views.add_review, name='add_review'),
    path('review/', views.review_view, name='review'),
    path('review/<slug:slug>/', views.review_view, name='review_view'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('get_models/', views.get_models, name='get_models'),
    path('get-racket/<slug:slug>/', views.get_racket, name='get_racket'),
    path('profile/', views.profile_view, name='profile'),
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('upload-profile-photo/', views.upload_profile_photo, name='upload-profile-photo'),
    path('delete-profile-photo/', views.delete_profile_photo, name='delete-profile-photo'),
    path('get_review/', views.get_review, name='get_review'),
    path('change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
    path('review-entry/', views.review_gate, name='review_entry'),

]
