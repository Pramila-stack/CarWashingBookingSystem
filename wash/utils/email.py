"""
Email notification utilities for SparkleWash.

Two public functions cover the booking lifecycle:
  - send_booking_confirmation(booking)   → customer
  - send_admin_booking_notification(booking) → admin(s)

Both are fire-and-forget: a failed send is logged but never
raises so it cannot break the booking transaction.
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ─── internal helpers ────────────────────────────────────────────────────────

def _build_context(booking) -> dict:
    """Single source of truth for template context shared by both emails."""
    customer = booking.customer
    return {
        "booking": booking,
        "booking_id": f"SWB-{booking.pk:05d}",
        "customer_name": customer.get_full_name() or customer.username,
        "customer_email": customer.email,
        "service_name": booking.service_package.name,
        "service_price": booking.service_package.price,
        "service_description": booking.service_package.description,
        "vehicle_type": booking.get_vehicle_type_display(),
        "appointment_date": booking.appointment_date.strftime("%A, %B %d, %Y"),
        "notes": booking.notes or "None",
        "status": booking.get_status_display(),
        "site_name": getattr(settings, "SITE_NAME", "SparkleWash"),
        "admin_email": settings.DEFAULT_FROM_EMAIL,
        "admin_dashboard_url": getattr(
            settings, "ADMIN_DASHBOARD_URL", "http://127.0.0.1:8000/admin/"
        ),
    }


def _send(subject: str, template_name: str, context: dict, to: list[str]) -> bool:
    """
    Render an HTML template, strip it to plain-text, and send both parts.
    Returns True on success, False on any error.
    """
    try:
        html_body = render_to_string(template_name, context)
        plain_body = strip_tags(html_body)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to,
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info("Email sent | subject=%r | to=%s", subject, to)
        return True
    except Exception as exc:
        logger.error(
            "Email failed | subject=%r | to=%s | error=%s",
            subject, to, exc, exc_info=True,
        )
        return False


# ─── public API ──────────────────────────────────────────────────────────────

def send_booking_confirmation(booking) -> bool:
    """
    Send a booking confirmation to the customer.
    Call this immediately after booking.save().
    """
    if not booking.customer.email:
        logger.warning("Booking #%s: customer has no email address.", booking.pk)
        return False

    context = _build_context(booking)
    subject = (
        f"[{context['site_name']}] Booking Confirmed – "
        f"{context['booking_id']} · {context['appointment_date']}"
    )
    return _send(
        subject=subject,
        template_name="emails/booking_confirmation.html",
        context=context,
        to=[booking.customer.email],
    )


def send_admin_booking_notification(booking) -> bool:
    """
    Alert admin staff about a new booking.
    Reads ADMIN_NOTIFICATION_EMAILS from settings; falls back to ADMINS tuples.
    """
    recipients = getattr(settings, "ADMIN_NOTIFICATION_EMAILS", None)

    if not recipients:
        # Fall back to Django's ADMINS setting: list of (name, email) tuples
        recipients = [email for _, email in getattr(settings, "ADMINS", [])]

    if not recipients:
        logger.warning(
            "No admin recipients configured. "
            "Set ADMIN_NOTIFICATION_EMAILS or ADMINS in settings.py."
        )
        return False

    context = _build_context(booking)
    subject = (
        f"[{context['site_name']}] New Booking Alert – "
        f"{context['booking_id']} from {context['customer_name']}"
    )
    return _send(
        subject=subject,
        template_name="emails/admin_notification.html",
        context=context,
        to=recipients,
    )


def send_booking_cancellation(booking) -> bool:
    """
    Notify the customer their booking was cancelled.
    Ready for future use – hook into cancel_booking view when needed.
    """
    if not booking.customer.email:
        return False

    context = _build_context(booking)
    subject = (
        f"[{context['site_name']}] Booking Cancelled – {context['booking_id']}"
    )
    return _send(
        subject=subject,
        template_name="emails/booking_cancellation.html",
        context=context,
        to=[booking.customer.email],
    )


def send_booking_status_update(booking) -> bool:
    """
    Notify the customer when their booking status changes (approved / completed).
    Ready for future use – hook into admin status-change logic when needed.
    """
    if not booking.customer.email:
        return False

    context = _build_context(booking)
    subject = (
        f"[{context['site_name']}] Booking Update – "
        f"{context['booking_id']} is now {context['status']}"
    )
    return _send(
        subject=subject,
        template_name="emails/booking_status_update.html",
        context=context,
        to=[booking.customer.email],
    )
