from django.db import models
from django.contrib.auth.models import User


class ServicePackage(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.name} (${self.price})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    VEHICLE_TYPES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('motorcycle', 'Motorcycle'),
        ('other', 'Other'),
    ]

    TIME_SLOTS = [
        ('morning', 'Morning (9 AM – 11 AM)'),
        ('afternoon', 'Afternoon (12 PM – 3 PM)'),
        ('evening', 'Evening (4 PM – 6 PM)'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    service_package = models.ForeignKey(ServicePackage, on_delete=models.PROTECT)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    appointment_date = models.DateField()
    appointment_time = models.CharField(max_length=20, choices=TIME_SLOTS, default='morning')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.username} - {self.service_package.name} ({self.appointment_date})"


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review #{self.pk} — {self.rating}★ for booking #{self.booking.pk}"