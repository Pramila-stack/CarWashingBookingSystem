from django.contrib import admin
from .models import ServicePackage, Booking


@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    search_fields = ['name']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['customer', 'service_package', 'vehicle_type', 'appointment_date', 'status', 'created_at']
    list_filter = ['status', 'vehicle_type', 'appointment_date']
    search_fields = ['customer__username', 'customer__email']
    list_editable = ['status']
    ordering = ['-created_at']
