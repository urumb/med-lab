"""
Admin configuration for the Medical Lab Booking System
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Category, Patient, Test, Booking


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model"""
    list_display = ['name', 'slug', 'test_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def test_count(self, obj):
        count = obj.tests.count()
        return format_html('<b>{}</b> tests', count)
    test_count.short_description = 'Associated Tests'


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Admin interface for Patient model"""
    list_display = [
        'name', 'user', 'age', 'gender', 'phone', 'email',
        'booking_count', 'created_at'
    ]
    list_filter = ['gender', 'created_at']
    search_fields = ['name', 'phone', 'email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Account Info', {
            'fields': ('user', 'name', 'age', 'gender')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address')
        }),
        ('System Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def booking_count(self, obj):
        count = obj.bookings.count()
        if count > 0:
            url = reverse('admin:booking_booking_changelist') + f'?patient__id={obj.id}'
            return format_html('<a href="{}">{} bookings</a>', url, count)
        return '0 bookings'
    booking_count.short_description = 'Bookings'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """Admin interface for Test model"""
    list_display = [
        'test_name', 'code', 'category', 'price_display', 'turnaround_time',
        'booking_count', 'is_active', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['test_name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['test_name']

    fieldsets = (
        ('Test Information', {
            'fields': ('test_name', 'code', 'category', 'description', 'preparation_instructions')
        }),
        ('Pricing & Service SLAs', {
            'fields': ('price', 'turnaround_time', 'duration_hours')
        }),
        ('Availability Status', {
            'fields': ('is_active',)
        }),
        ('System Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        return f"₹{obj.price}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'

    def booking_count(self, obj):
        count = obj.bookings.count()
        if count > 0:
            url = reverse('admin:booking_booking_changelist') + f'?test__id={obj.id}'
            return format_html('<a href="{}">{} bookings</a>', url, count)
        return '0 bookings'
    booking_count.short_description = 'Total Bookings'

    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} tests marked as active.')
    make_active.short_description = 'Mark selected tests as active'

    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} tests marked as inactive.')
    make_inactive.short_description = 'Mark selected tests as inactive'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking model"""
    list_display = [
        'reference_number', 'patient_name', 'test_name', 'booking_datetime',
        'status_display', 'total_cost_display', 'created_at'
    ]
    list_filter = ['status', 'booking_date', 'test__category', 'created_at']
    search_fields = [
        'reference_number', 'patient__name', 'patient__phone', 'patient__email',
        'test__test_name'
    ]
    readonly_fields = ['reference_number', 'created_at', 'updated_at', 'total_cost_display']
    ordering = ['-booking_date', '-booking_time']
    date_hierarchy = 'booking_date'

    fieldsets = (
        ('Reference & Schedule', {
            'fields': ('reference_number', 'patient', 'test', 'booking_date', 'booking_time')
        }),
        ('Workflow & Notes', {
            'fields': ('status', 'notes')
        }),
        ('Billing Details', {
            'fields': ('total_cost_display',),
            'classes': ('collapse',)
        }),
        ('System Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def patient_name(self, obj):
        url = reverse('admin:booking_patient_change', args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.name)
    patient_name.short_description = 'Patient'

    def test_name(self, obj):
        url = reverse('admin:booking_test_change', args=[obj.test.id])
        return format_html('<a href="{}">{}</a>', url, obj.test.test_name)
    test_name.short_description = 'Test'

    def booking_datetime(self, obj):
        return f"{obj.booking_date} at {obj.booking_time.strftime('%I:%M %p')}"
    booking_datetime.short_description = 'Scheduled Date & Time'

    def status_display(self, obj):
        badge_class = obj.get_status_badge_class()
        return format_html(
            '<span class="badge {}" style="padding: 5px 10px; font-weight: bold;">{}</span>',
            badge_class, obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def total_cost_display(self, obj):
        return f"₹{obj.total_cost}"
    total_cost_display.short_description = 'Total Cost'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient', 'test')


admin.site.site_header = "Medical Lab Management System"
admin.site.site_title = "Medical Lab Admin Portal"
admin.site.index_title = "Laboratory Management & Diagnostics"
