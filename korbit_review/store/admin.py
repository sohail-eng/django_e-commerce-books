from django.contrib import admin
from .models import Category, Book, Order, OrderItem, Review

# Register your models here.


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Category, CategoryAdmin)


class BookAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'price',
        'stock',
        'available',
        'created',
        'updated']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20


admin.site.register(Book, BookAdmin)


class OrderItemAdmin(admin.TabularInline):
    model = OrderItem
    fieldsets = [
        ('Book', {'fields': ['book'], }),
        ('Quantity', {'fields': ['quantity'], }),
        ('Price', {'fields': ['price'], }),
    ]
    readonly_fields = ['book', 'quantity', 'price']
    can_delete = False
    max_num = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'billingName', 'emailAddress', 'created']
    list_display_links = ['id', 'billingName']
    search_fields = ['id', 'billingName', 'emailAddress']
    readonly_fields = [
        'id',
        'token',
        'total',
        'emailAddress',
        'created',
        'billingName',
        'billingAddress1',
        'billingCity',
        'billingPostcode',
        'billingCountry',
        'shippingName',
        'shippingAddress1',
        'shippingCity',
        'shippingPostcode',
        'shippingCountry']

    fieldsets = [
        ('ORDER INFORMATION', {'fields': ['id', 'token', 'total', 'created']}),
        ('BILLING INFORMATION', {'fields': ['billingName',
                                            'billingAddress1',
                                            'billingCity',
                                            'billingPostcode',
                                            'billingCountry', ]}),
        ('SHIPPING INFORMATION', {'fields': ['shippingName',
                                             'shippingAddress1',
                                             'shippingCity',
                                             'shippingPostcode',
                                             'shippingCountry']})
    ]

    inlines = [
        OrderItemAdmin,
    ]

    def has_add_permission(self, request):
        return False


admin.site.register(Order, OrderAdmin)
admin.site.register(Review)
