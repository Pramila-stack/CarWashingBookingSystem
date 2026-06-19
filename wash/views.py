import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BookingForm, ProfileForm, RegisterForm
from .models import Booking, ServicePackage
from .utils.email import (
    send_admin_booking_notification,
    send_booking_cancellation,
    send_booking_confirmation,
    send_booking_status_update,
)

logger = logging.getLogger(__name__)


# ─── helpers ─────────────────────────────────────────────────────────────────

def _is_staff(user):
    return user.is_active and (user.is_staff or user.is_superuser)


staff_required = user_passes_test(_is_staff, login_url='/login/')


# ─── public ──────────────────────────────────────────────────────────────────

def home(request):
    packages = ServicePackage.objects.all()
    return render(request, 'home.html', {'packages': packages})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name or user.username}!")
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        if _is_staff(request.user):
            return redirect('admin_dashboard')
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if _is_staff(user):
                messages.success(request, f"Welcome back, {user.first_name or user.username}. You're in admin mode.")
                return redirect('admin_dashboard')
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect('home')


# ─── customer ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    if _is_staff(request.user):
        return redirect('admin_dashboard')
    bookings = request.user.bookings.select_related('service_package')
    today = timezone.now().date()
    upcoming = bookings.filter(appointment_date__gte=today, status__in=['pending', 'approved'])
    return render(request, 'wash/dashboard.html', {
        'bookings': bookings[:5],
        'upcoming': upcoming[:3],
        'total': bookings.count(),
        'pending_count': bookings.filter(status='pending').count(),
        'completed_count': bookings.filter(status='completed').count(),
        'approved_count': bookings.filter(status='approved').count(),
    })


@login_required
def book_service(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.save()
            send_booking_confirmation(booking)
            send_admin_booking_notification(booking)
            messages.success(
                request,
                f"Booking #{booking.pk} confirmed — a confirmation has been sent to your email."
            )
            return redirect('booking_history')
    else:
        form = BookingForm()
    return render(request, 'wash/book_service.html', {
        'form': form,
        'packages': ServicePackage.objects.all(),
    })


@login_required
def booking_history(request):
    status_filter = request.GET.get('status', '')
    qs = request.user.bookings.select_related('service_package')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'wash/booking_history.html', {
        'bookings': qs,
        'status_filter': status_filter,
        'status_choices': Booking.STATUS_CHOICES,
    })


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    if booking.status == 'pending':
        booking.status = 'cancelled'
        booking.save()
        send_booking_cancellation(booking)
        messages.success(request, "Booking cancelled. A confirmation has been sent to your email.")
    else:
        messages.error(request, "Only pending bookings can be cancelled.")
    return redirect('booking_history')


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'wash/profile.html', {
        'form': form,
        'total_bookings': request.user.bookings.count(),
    })


# ─── admin panel ─────────────────────────────────────────────────────────────

@login_required
@staff_required
def admin_dashboard(request):
    bookings = Booking.objects.select_related('customer', 'service_package')
    today = timezone.now().date()

    stats = {
        'total':     bookings.count(),
        'pending':   bookings.filter(status='pending').count(),
        'approved':  bookings.filter(status='approved').count(),
        'completed': bookings.filter(status='completed').count(),
        'cancelled': bookings.filter(status='cancelled').count(),
        'today':     bookings.filter(appointment_date=today).count(),
        'revenue':   sum(
            b.service_package.price
            for b in bookings.filter(status='completed').select_related('service_package')
        ),
        'customers': User.objects.filter(is_staff=False).count(),
    }

    recent = bookings.order_by('-created_at')[:8]
    upcoming = bookings.filter(
        appointment_date__gte=today, status__in=['pending', 'approved']
    ).order_by('appointment_date')[:6]

    return render(request, 'admin_panel/dashboard.html', {
        'stats': stats,
        'recent': recent,
        'upcoming': upcoming,
    })


@login_required
@staff_required
def admin_bookings(request):
    qs = Booking.objects.select_related('customer', 'service_package').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()

    if status_filter:
        qs = qs.filter(status=status_filter)
    if search:
        qs = qs.filter(
            Q(customer__username__icontains=search) |
            Q(customer__first_name__icontains=search) |
            Q(customer__last_name__icontains=search) |
            Q(customer__email__icontains=search) |
            Q(service_package__name__icontains=search)
        )

    return render(request, 'admin_panel/bookings.html', {
        'bookings': qs,
        'status_filter': status_filter,
        'search': search,
        'status_choices': Booking.STATUS_CHOICES,
        'total_count': qs.count(),
    })


@login_required
@staff_required
def admin_booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('customer', 'service_package'), pk=pk
    )
    return render(request, 'admin_panel/booking_detail.html', {'booking': booking})


@login_required
@staff_required
def admin_update_status(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid = [s for s, _ in Booking.STATUS_CHOICES]
        if new_status not in valid:
            messages.error(request, "Invalid status.")
            return redirect('admin_booking_detail', pk=pk)

        old_status = booking.status
        booking.status = new_status
        booking.save()

        # Email customer on every meaningful status change
        if new_status != old_status:
            if new_status == 'cancelled':
                send_booking_cancellation(booking)
            else:
                send_booking_status_update(booking)
            # Always re-alert admin of major changes
            if new_status in ('approved', 'completed'):
                send_admin_booking_notification(booking)

        messages.success(
            request,
            f"Booking #{pk} status updated to '{new_status.title()}'. "
            "Customer has been notified by email."
        )
        return redirect('admin_bookings')

    return redirect('admin_booking_detail', pk=pk)


@login_required
@staff_required
def admin_delete_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, f"Booking #{pk} has been permanently deleted.")
        return redirect('admin_bookings')
    return redirect('admin_booking_detail', pk=pk)


@login_required
@staff_required
def admin_customers(request):
    customers = User.objects.filter(is_staff=False).annotate(
        booking_count=Count('bookings')
    ).order_by('-date_joined')
    return render(request, 'admin_panel/customers.html', {'customers': customers})


@login_required
@staff_required
def admin_packages(request):
    packages = ServicePackage.objects.annotate(booking_count=Count('booking'))
    return render(request, 'admin_panel/packages.html', {'packages': packages})


@login_required
@staff_required
def admin_package_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '0')
        if name and description and price:
            ServicePackage.objects.create(name=name, description=description, price=price)
            messages.success(request, f"Package '{name}' created.")
            return redirect('admin_packages')
        messages.error(request, "All fields are required.")
    return render(request, 'admin_panel/package_form.html', {'action': 'Create', 'pkg': None})


@login_required
@staff_required
def admin_package_edit(request, pk):
    pkg = get_object_or_404(ServicePackage, pk=pk)
    if request.method == 'POST':
        pkg.name = request.POST.get('name', pkg.name).strip()
        pkg.description = request.POST.get('description', pkg.description).strip()
        pkg.price = request.POST.get('price', pkg.price)
        pkg.save()
        messages.success(request, f"Package '{pkg.name}' updated.")
        return redirect('admin_packages')
    return render(request, 'admin_panel/package_form.html', {'action': 'Edit', 'pkg': pkg})


@login_required
@staff_required
def admin_package_delete(request, pk):
    pkg = get_object_or_404(ServicePackage, pk=pk)
    if request.method == 'POST':
        name = pkg.name
        pkg.delete()
        messages.success(request, f"Package '{name}' deleted.")
        return redirect('admin_packages')
    return redirect('admin_packages')
