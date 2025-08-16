from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Category, Book, Cart, CartItem, Order, OrderItem, Review
import stripe
from django.conf import settings
from django.contrib.auth.models import User, Group
from .forms import SignUpForm, ContactForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required


# Create your views here.

def home(request, category_slug=None):
    category_page = None
    books = None
    if category_slug is not None:
        category_page = get_object_or_404(Category, slug=category_slug)
        books = Book.objects.filter(
            category=category_page, available=True)
    else:
        books = Book.objects.all().filter(available=True)
    return render(request, 'home.html', {
                  'category': category_page, 'books': books})


def book_page(request, category_slug, book_slug):
    try:
        book = Book.objects.get(
            category__slug=category_slug,
            slug=book_slug)
    except Exception as e:
        raise e

    if request.method == 'POST' and request.user.is_authenticated and request.POST['content'].strip(
    ) != '':
        Review.objects.create(book=book,
                              user=request.user,
                              content=request.POST['content'])

    reviews = Review.objects.filter(book=book)

    return render(request, 'book.html', {
                  'book': book, 'reviews': reviews})


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, book_id):
    book = Book.objects.get(pk=book_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
        cart.save()
    try:
        cart_item = CartItem.objects.get(book=book, cart=cart)
        if cart_item.quantity < cart_item.book.stock:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            book=book,
            quantity=1,
            cart=cart
        )
        cart_item.save()

    return redirect('cart_detail')


def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for cart_item in cart_items:
            total += (cart_item.book.price * cart_item.quantity)
            counter += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_total = int(total * 100)
    description = 'Z-Store - New Order'
    data_key = settings.STRIPE_PUBLISHABLE_KEY
    if request.method == 'POST':
        try:
            token = request.POST['stripeToken']
            email = request.POST['stripeEmail']

            billingName = request.POST['stripeBillingName']
            billingAddress1 = request.POST['stripeBillingAddressLine1']
            billingCity = request.POST['stripeBillingAddressCity']
            billingPostcode = request.POST['stripeBillingAddressZip']
            billingCountry = request.POST['stripeBillingAddressCountryCode']

            shippingName = request.POST['stripeShippingName']
            shippingAddress1 = request.POST['stripeShippingAddressLine1']
            shippingCity = request.POST['stripeShippingAddressCity']
            shippingPostcode = request.POST['stripeShippingAddressZip']
            shippingCountry = request.POST['stripeShippingAddressCountryCode']

            customer = stripe.Customer.create(
                email=email,
                source=token
            )
            charge = stripe.Charge.create(
                amount=stripe_total,
                currency='usd',
                description=description,
                customer=customer.id
            )
            # Creating Order
            try:
                order_details = Order.objects.create(
                    token=token,
                    total=total,
                    emailAddress=email,

                    billingName=billingName,
                    billingAddress1=billingAddress1,
                    billingCity=billingCity,
                    billingPostcode=billingPostcode,
                    billingCountry=billingCountry,

                    shippingName=shippingName,
                    shippingAddress1=shippingAddress1,
                    shippingCity=shippingCity,
                    shippingPostcode=shippingPostcode,
                    shippingCountry=shippingCountry,
                )
                order_details.save()
                for order_item in cart_items:
                    or_item = OrderItem.objects.create(
                        book=order_item.book.name,
                        quantity=order_item.quantity,
                        price=order_item.book.price,
                        order=order_details
                    )
                    order_item.save()

                    # reduce stock
                    books = Book.objects.get(id=order_item.book.id)
                    books.stock = int(
                        order_item.book.stock - order_item.quantity)
                    books.save()
                    order_item.delete()

                    # print message when the order is created
                    print('the order has been created')
                return redirect('thanks_page', order_details.id)
            except ObjectDoesNotExist:
                pass

        except stripe.error.CardError as e:
            return False, e

    return render(
        request,
        'cart.html',
        dict(
            cart_items=cart_items,
            total=total,
            counter=counter,
            data_key=data_key,
            stripe_total=stripe_total,
            description=description))


def cart_remove(request, book_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    book = get_object_or_404(Book, id=book_id)
    cart_item = CartItem.objects.get(book=book, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_detail')


def cart_remove_book(request, book_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    book = get_object_or_404(Book, id=book_id)
    cart_item = CartItem.objects.get(book=book, cart=cart)
    cart_item.delete()
    return redirect('cart_detail')


def thanks_page(request, order_id):
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
    return render(request, 'thankyou.html', {'custumer_order': customer_order})


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            customer_group = Group.objects.get(name='Customer')
            customer_group.user_set.add(signup_user)
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def signin_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signup')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form': form})


def signout_view(request):
    logout(request)
    return redirect('signin')


@login_required(redirect_field_name='next', login_url='signin')
def order_history(request):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order_details = Order.objects.filter(emailAddress=email)
    return render(request, 'orders_list.html', {
                  'order_details': order_details})


@login_required(redirect_field_name='next', login_url='signin')
def view_order(request, order_id):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order = Order.objects.get(id=order_id, emailAddress=email)
        order_items = OrderItem.objects.filter(order=order)
    return render(request, 'orders_detail.html', {
                  'order': order, 'order_items': order_items})


def search(request):
    books = Book.objects.filter(name__contains=request.GET['title'])
    return render(request, 'home.html', {'books': books})


def contact(request):

    form = ContactForm()
    return render(request, 'contact.html', {'form': form})
