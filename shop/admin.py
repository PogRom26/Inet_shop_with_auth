# shop/admin.py
from django.contrib import admin
from .models import Category, Product, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'category__name')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product_name', 'price', 'quantity', 'total_price')
    can_delete = False
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('user', 'address', 'total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered']

    def mark_as_confirmed(self, request, queryset):
        queryset.filter(status='pending').update(status='confirmed')
    mark_as_confirmed.short_description = 'Подтвердить заказы'

    def mark_as_shipped(self, request, queryset):
        queryset.filter(status='confirmed').update(status='shipped')
    mark_as_shipped.short_description = 'Отправить заказы'

    def mark_as_delivered(self, request, queryset):
        queryset.filter(status='shipped').update(status='delivered')
    mark_as_delivered.short_description = 'Отметить как доставленные'


