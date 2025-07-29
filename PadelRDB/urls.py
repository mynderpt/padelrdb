from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from PadelRDB_app import views
from PadelRDB_app.views import (
    profile_view, change_password_ajax, review_view, delete_review,
    upload_profile_photo, delete_profile_photo, get_review, CustomPasswordChangeView, CustomLoginView, create_account,
)

# Include only this outside
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

# Wrap everything else in i18n_patterns
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('browse/', views.browse, name='browse'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create/', create_account, name='create'),
    path('redirect/', views.nologin, name='redirect'),
    path('rackets/all/', views.all_rackets, name='all_rackets'),
    path('browse/<str:name>/', views.brand_page, name='brand_page'),
    path('browse/<str:name>/<slug:slug>/', views.racket_detail, name='racket_detail'),
    path('racket/<slug:slug>/review/', views.add_review, name='add_review'),
    path('review/', views.review_view, name='review'),
    path('review/<slug:slug>/', views.review_view, name='review_view'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('get_models', views.get_models, name='get_models'),
    path('get-racket/<slug:slug>/', views.get_racket, name='get_racket'),
    path('profile/', views.profile_view, name='profile'),
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('upload-profile-photo/', views.upload_profile_photo, name='upload-profile-photo'),
    path('delete-profile-photo/', views.delete_profile_photo, name='delete-profile-photo'),
    path('get_review/', views.get_review, name='get_review'),
    path('change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
    path('review-entry/', views.review_gate, name='review_entry'),
    

)

# Static files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
