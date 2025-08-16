from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path(
        'category/<slug:category_slug>',
        views.home,
        name='books_by_category'),
    path('category/<slug:category_slug>/<slug:book_slug>',
         views.book_page, name='books_detail'),
    path('cart/add/<int:book_id>', views.add_cart, name='add_cart'),
    path(
        'cart/remove/<int:book_id>',
        views.cart_remove,
        name='cart_remove'),
    path(
        'cart/remove_book/<int:book_id>',
        views.cart_remove_book,
        name='cart_remove_book'),
    path('cart', views.cart_detail, name='cart_detail'),
    path('thankyou/<int:order_id>', views.thanks_page, name='thanks_page'),
    path('account/create/', views.signup_view, name='signup'),
    path('account/signin/', views.signin_view, name='signin'),
    path('account/signout/', views.signout_view, name='signout'),
    path('order_history/', views.order_history, name='order_history'),
    path('order/<int:order_id>', views.view_order, name='order_detail'),
    path('search/', views.search, name='search'),
    path('contact/', views.contact, name='contact')
]
