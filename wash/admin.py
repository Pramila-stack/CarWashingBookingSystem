from django.contrib import admin
from .models import Booking, Review, ServicePackage


@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    search_fields = ['name']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['customer', 'service_package', 'vehicle_type', 'appointment_date', 'appointment_time', 'status', 'created_at']
    list_filter = ['status', 'vehicle_type', 'appointment_date', 'appointment_time']
    search_fields = ['customer__username', 'customer__email']
    list_editable = ['status']
    ordering = ['-created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['booking', 'rating', 'created_at']
    list_filter = ['rating']
    ordering = ['-created_at']
    readonly_fields = ['booking', 'created_at']
