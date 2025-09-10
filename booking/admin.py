"""
Admin configuration for the Medical Lab Booking System
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Patient, Test, Booking


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Admin interface for Patient model"""
    list_display = [
        'name', 'age', 'gender', 'phone', 'email', 
        'booking_count', 'created_at'
    ]
    list_filter = ['gender', 'age', 'created_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'age', 'gender')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def booking_count(self, obj):
        """Display count of bookings for this patient"""
        count = obj.booking_set.count()
        if count > 0:
            url = reverse('admin:booking_booking_changelist') + f'?patient__id={obj.id}'
            return format_html('<a href="{}">{} bookings</a>', url, count)
        return '0 bookings'
    booking_count.short_description = 'Bookings'

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        return super().get_queryset(request).prefetch_related('booking_set')


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """Admin interface for Test model"""
    list_display = [
        'test_name', 'price_display', 'duration_hours', 
        'booking_count', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'duration_hours', 'created_at']
    search_fields = ['test_name', 'description']
    readonly_fields = ['created_at']
    ordering = ['test_name']

    fieldsets = (
        ('Test Information', {
            'fields': ('test_name', 'description')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'duration_hours')
        }),
        ('Availability', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        """Display price with currency symbol"""
        return f"₹{obj.price}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'

    def booking_count(self, obj):
        """Display count of bookings for this test"""
        count = obj.booking_set.count()
        if count > 0:
            url = reverse('admin:booking_booking_changelist') + f'?test__id={obj.id}'
            return format_html('<a href="{}">{} bookings</a>', url, count)
        return '0 bookings'
    booking_count.short_description = 'Total Bookings'

    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        """Mark selected tests as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} tests marked as active.')
    make_active.short_description = 'Mark selected tests as active'

    def make_inactive(self, request, queryset):
        """Mark selected tests as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} tests marked as inactive.')
    make_inactive.short_description = 'Mark selected tests as inactive'


class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking model"""
    list_display = [
        'booking_id', 'patient_name', 'test_name', 'booking_datetime',
        'status_display', 'total_cost_display', 'is_upcoming_display', 'created_at'
    ]
    list_filter = ['status', 'booking_date', 'test', 'created_at']
    search_fields = [
        'patient__name', 'patient__phone', 'patient__email',
        'test__test_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'total_cost_display']
    ordering = ['-booking_date', '-booking_time']
    date_hierarchy = 'booking_date'

    fieldsets = (
        ('Booking Information', {
            'fields': ('patient', 'test', 'booking_date', 'booking_time')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes')
        }),
        ('Cost Information', {
            'fields': ('total_cost_display',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def booking_id(self, obj):
        """Display booking ID"""
        return f"BK-{obj.id:04d}"
    booking_id.short_description = 'Booking ID'
    booking_id.admin_order_field = 'id'

    def patient_name(self, obj):
        """Display patient name with link"""
        url = reverse('admin:booking_patient_change', args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.name)
    patient_name.short_description = 'Patient'
    patient_name.admin_order_field = 'patient__name'

    def test_name(self, obj):
        """Display test name with link"""
        url = reverse('admin:booking_test_change', args=[obj.test.id])
        return format_html('<a href="{}">{}</a>', url, obj.test.test_name)
    test_name.short_description = 'Test'
    test_name.admin_order_field = 'test__test_name'

    def booking_datetime(self, obj):
        """Display booking date and time"""
        return f"{obj.booking_date} at {obj.booking_time}"
    booking_datetime.short_description = 'Date & Time'
    booking_datetime.admin_order_field = 'booking_date'

    def status_display(self, obj):
        """Display status with color coding"""
        color = obj.get_status_color()
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'

    def total_cost_display(self, obj):
        """Display total cost"""
        return f"₹{obj.total_cost}"
    total_cost_display.short_description = 'Total Cost'

    def is_upcoming_display(self, obj):
        """Display if booking is upcoming"""
        if obj.is_upcoming:
            return format_html('<span style="color: green;">✓ Upcoming</span>')
        return format_html('<span style="color: red;">✗ Past</span>')
    is_upcoming_display.short_description = 'Upcoming'

    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled']

    def mark_confirmed(self, request, queryset):
        """Mark selected bookings as confirmed"""
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} bookings marked as confirmed.')
    mark_confirmed.short_description = 'Mark as Confirmed'

    def mark_completed(self, request, queryset):
        """Mark selected bookings as completed"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} bookings marked as completed.')
    mark_completed.short_description = 'Mark as Completed'

    def mark_cancelled(self, request, queryset):
        """Mark selected bookings as cancelled"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} bookings marked as cancelled.')
    mark_cancelled.short_description = 'Mark as Cancelled'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('patient', 'test')


# Register the Booking model with custom admin
admin.site.register(Booking, BookingAdmin)

# Custom admin site configuration
admin.site.site_header = "Medical Lab Management System"
admin.site.site_title = "Medical Lab Admin"
admin.site.index_title = "Welcome to Medical Lab Administration"
