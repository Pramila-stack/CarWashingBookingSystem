from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Customer
    path('dashboard/', views.dashboard, name='dashboard'),
    path('book/', views.book_service, name='book_service'),
    path('history/', views.booking_history, name='booking_history'),
    path('cancel/<int:pk>/', views.cancel_booking, name='cancel_booking'),
    path('profile/', views.profile, name='profile'),

    # Admin panel
    path('panel/', views.admin_dashboard, name='admin_dashboard'),
    path('panel/bookings/', views.admin_bookings, name='admin_bookings'),
    path('panel/bookings/<int:pk>/', views.admin_booking_detail, name='admin_booking_detail'),
    path('panel/bookings/<int:pk>/status/', views.admin_update_status, name='admin_update_status'),
    path('panel/bookings/<int:pk>/delete/', views.admin_delete_booking, name='admin_delete_booking'),
    path('panel/customers/', views.admin_customers, name='admin_customers'),
    path('panel/packages/', views.admin_packages, name='admin_packages'),
    path('panel/packages/create/', views.admin_package_create, name='admin_package_create'),
    path('panel/packages/<int:pk>/edit/', views.admin_package_edit, name='admin_package_edit'),
    path('panel/packages/<int:pk>/delete/', views.admin_package_delete, name='admin_package_delete'),
]
