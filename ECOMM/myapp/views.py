from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.generic.base import TemplateView, View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from myapp.serializers import ProductSerializers

from .models import *
from .serializers import *


class BaseView(View):
    views = dict()
    views['sliders'] = Slider.objects.filter(status='active')
    views['brands'] = Brand.objects.filter(status='active')
    views['item_count'] = Product.objects.count()
    views['items'] = Product.objects.filter(status='active')
    views['cat_details'] = Category.objects.filter(status='active')
    views['cats_count'] = []
    for i in views['cat_details']:
        count_item = Product.objects.filter(category=i.id).count()
        a = {'cats': i.title, 'image': i.image,
             'cat_count': count_item, 'url': i.get_cat_url}
        views['cats_count'].append(a)

    views['brand_details'] = Brand.objects.filter(status='active')
    views['brands_count'] = []
    for i in views['brand_details']:
        count_brand = Product.objects.filter(brand=i.id).count()
        b = {'brands': i.name, 'brand_count': count_brand}
        views['brands_count'].append(b)


class HomeView(BaseView):
    def get(self, request):
        user = request.user.username
        self.views['ads'] = Ad.objects.filter(status='active')
        self.views['hots'] = Product.objects.filter(
            label='hot', status='active')
        self.views['news'] = Product.objects.filter(
            label='new', status='active')
        self.views['most_viewed'] = Product.objects.filter(
            label='most_viewed', status='active')
        self.views['defaults'] = Product.objects.filter(
            label='', status='passive')
        self.views['site_reviews'] = SiteReview.objects.filter(status='active')
        return render(request, 'index.html', self.views)


class ItemDetailView(BaseView):
    def get(self, request, slug):
        self.views['item_detail'] = Product.objects.filter(slug=slug)
        item_ids = Product.objects.get(slug=slug).category_id
        self.views['item_cats'] = Product.objects.filter(category=item_ids)
        self.views['reviews'] = Review.objects.filter(
            slug=slug, status='active')
        return render(request, 'product-detail.html', self.views)


class ItemListView(BaseView):
    def get(self, request, slug):
        cat_ids = Category.objects.get(slug=slug).id
        self.views['cat_items'] = Product.objects.filter(category=cat_ids)
        return render(request, 'product-list.html', self.views)


class SearchView(BaseView):
    def get(self, request):
        if request.method == 'GET':
            query = request.GET['search']
            self.views['search_product'] = Product.objects.filter(
                name__icontains=query)
            return render(request, 'search.html', self.views)
        return render(request, 'search.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']

        contact_data = Contact.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        if len(name) < 3 or len(message) < 5 or len(email) < 4:
            messages.error(request, '❌ Please re-enter the contact form!')
            return redirect('myapp:contact')
        else:
            send_email = EmailMessage(
                'contact from your website',
                f'Hello, the contact of {name} is saved, the email is {email}. and the contact has the subject named "{subject}".'
                f' The message is {message}.',
                settings.EMAIL_HOST_USER,
                ['brunofernandez1001@gmail.com'],
                # [request.user.email],
                [email],
            )
            send_email.fail_silently = False
            send_email.send()
            contact_data.save()
            return redirect('/', kwargs={'messages': messages.success(request, '✔ Contact Saved and an'
                                                                               ' email is sent to you.')})
    return render(request, 'contact.html')


def signup(request):
    Cart.objects.all().delete()
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        cpassword = request.POST['cpassword']
        fname = request.POST['fname']
        lname = request.POST['lname']

        if password == cpassword:
            if User.objects.filter(username=username).exists():
                messages.error(request, '❌ This username is already taken!')
                return redirect('myapp:account')
            elif User.objects.filter(email=email).exists():
                messages.error(request, '❌ This email is already taken!')
                return redirect('myapp:account')
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=fname,
                    last_name=lname
                )
                user.save()
                messages.success(
                    request, '✔️You are registered! Continue to login!')
                return redirect('/accounts/login', messages)
        else:
            messages.error(request, '❌ These passwords do not match!')
            return redirect('myapp:account')
    return render(request, 'signup.html')


# def login(request):
#     user = request.user.username
#     if user.is_authenticated:
#         messages.success(request, f'✔️You are logged in as! {user}')
#         return redirect('myapp:home', messages)

# def wishlist(request, slug):
#     price = Product.objects.get(slug=slug).price
#     discounted_price = Product.objects.get(slug=slug).discounted_price
#     user = request.user.username

#     if WishList.objects.filter(slug=slug).exists():
#         quantity = Product.objects.filter(username=user, slug=slug).quantity
#         qty = quantity + 1
#         if discounted_price > 0:
#             actual_total = discounted_price * qty
#         else:
#             actual_total = price * qty
#         WishList.objects.filter(username=user, slug=slug).update(
#             quantity=qty, total=actual_total)
#     else:
#         if discounted_price > 0:
#             actual_total = discounted_price * 1
#         else:
#             actual_total = price * 1
#         data = WishList.objects.create(
#             username=user,
#             slug=slug,
#             quantity=1,
#             total=actual_total,
#             product=Product.objects.filter(slug=slug)[0]

#         )
#         data.save()
#         messages.success(
#             request, f'✔️Your wish-item {slug} is successfully added!')
#         WishList.objects.filter(
#             username=user, slug=slug).update(total=actual_total)


class WishListView(BaseView):
    def get(self, request, slug):
        user = request.user.username
        wish_ids = Product.objects.get(slug=slug).id
        self.views['wish_items'] = WishList.objects.filter(product=wish_ids)

        if request.user.is_authenticated():
            self.views['wish_product'] = WishList.objects.filter(username=user)

        else:
            messages.error(request, 'please Sign up first!')
            return redirect('myapp:account')

        return render(request, 'wishlist.html', self.views)


def review_item(request):
    if request.method == 'POST':
        rating = request.POST['rating']
        review = request.POST['review']
        username = request.user.username
        email = request.user.email
        slug = request.POST['slug']

        user_review = Review.objects.create(
            rating=rating,
            username=username,
            review=review,
            email=email,
            slug=slug
        )
        user_review.save()
        messages.success(request, '✔️Your review is successfully submitted!')
        return redirect(f'/products/{slug}')


def cart(request, slug):
    price = Product.objects.get(slug=slug).price
    discounted_price = Product.objects.get(slug=slug).discounted_price
    user = request.user.username
    net_total = 0
    shipping_cost = 1000
    if Cart.objects.filter(slug=slug).exists():
        quantity = Cart.objects.get(
            username=user, slug=slug, checkout=False).quantity
        qty = quantity + 1
        if discounted_price > 0:
            actual_total = discounted_price * qty
        else:
            actual_total = price * qty
        Cart.objects.filter(username=user, slug=slug, checkout=False).update(
            quantity=qty, total=actual_total)

        total = Cart.objects.filter(
            username=user, checkout=False, status='active')

        for i in total[:]:
            net_total += i.total
        grand_total = net_total + shipping_cost

        CartTotal.objects.filter(username=user, checkout=False).update(
            net_total=net_total, shipping_cost=shipping_cost, grand_total=grand_total)
        return redirect('myapp:my_cart')

    else:
        if discounted_price > 0:
            actual_total = discounted_price * 1
        else:
            actual_total = price * 1
        data = Cart.objects.create(
            username=user,
            slug=slug,
            quantity=1,
            total=actual_total,
            products=Product.objects.filter(slug=slug)[0]

        )
        Cart.objects.filter(username=user, slug=slug, checkout=False).update(
            checkout=False, total=actual_total)
        total = Cart.objects.filter(
            username=user, checkout=False, status='active')

        for i in total[:]:
            net_total += i.total
        grand_total = net_total + shipping_cost
        data1 = CartTotal.objects.create(
            username=user,
            slug=slug,
            net_total=net_total,
            shipping_cost=shipping_cost,
            grand_total=grand_total,
            cart=Cart.objects.filter(slug=slug)[0]
        )
        if request.user.is_authenticated:
            data.save()
            data1.save()
            messages.success(request, f'✔️The item "{slug}" is added in cart!')
        else:
            messages.error(request, 'please Sign Up first!')
            return redirect('myapp:account')

        CartTotal.objects.filter(username=user, checkout=False).update(
            net_total=net_total, shipping_cost=shipping_cost, grand_total=grand_total)
        return redirect('myapp:my_cart')


class CartView(BaseView):
    def get(self, request):
        user = request.user.username
        net_total = 0
        shipping_cost = 1000
        grand_total = 0
        if request.user.is_authenticated:
            self.views['cart_product'] = Cart.objects.filter(
                username=user, checkout=False, status='active')
            tots = CartTotal.objects.filter(username=user, checkout=False)
            for i in tots[:]:
                net_total = i.net_total
                shipping_cost = i.shipping_cost
                grand_total = i.grand_total
            self.views['cart_total'] = [
                {'net_total': net_total, 'shipping_cost': shipping_cost, 'grand_total': grand_total}]
            self.views['cart_count'] = Cart.objects.filter(
                username=user, status='active', checkout=False).count()
        else:
            messages.error(request, 'please Sign up first!')
            return redirect('myapp:account')
        return render(request, 'cart.html', self.views)


def delete_cart(request, slug):
    if Cart.objects.filter(slug=slug).exists():
        user = request.user.username
        net_total = 0
        t = 0
        shipping_cost = 1000
        grand_total = 0
        b = Cart.objects.filter(username=user, slug=slug,
                                checkout=False, status='active')
        tots = CartTotal.objects.filter(username=user, checkout=False)
        for j in b[:]:
            t = j.total
        for i in tots[:]:
            net_total = i.net_total
            shipping_cost = i.shipping_cost
            grand_total = i.grand_total
        net_total = net_total - t
        grand_total = net_total + shipping_cost
        Cart.objects.filter(username=user, slug=slug, checkout=False).delete()
        CartTotal.objects.filter(username=user, checkout=False).update(net_total=net_total, grand_total=grand_total,
                                                                       shipping_cost=shipping_cost)

        if Cart.objects.count() == 0:
            messages.info(request, 'You have 0 items in the Cart!')
            net_total = net_total
            grand_total = grand_total
            shipping_cost = shipping_cost
            CartTotal.objects.filter(username=user, checkout=False).update(net_total=net_total, grand_total=grand_total,
                                                                           shipping_cost=shipping_cost)
            return redirect('myapp:my_cart')
    return redirect('myapp:my_cart')


def delete_single_cart(request, slug):
    if Cart.objects.filter(slug=slug).exists():
        net_total = 0
        shipping_cost = 1000
        user = request.user.username
        price = Product.objects.get(slug=slug).price
        discounted_price = Product.objects.get(slug=slug).discounted_price
        quantity = Cart.objects.get(
            username=user, slug=slug, checkout=False).quantity
        if quantity > 1:
            qty = quantity - 1
            if discounted_price == 0:
                actual_total = price*qty
            else:
                actual_total = discounted_price*qty
            Cart.objects.filter(username=user, slug=slug, checkout=False).update(
                quantity=qty, checkout=False, total=actual_total)
        total = Cart.objects.filter(
            username=user, checkout=False, status='active')

        for i in total[0:]:
            net_total += i.total
        grand_total = net_total + shipping_cost
        CartTotal.objects.filter(username=user, checkout=False).update(
            net_total=net_total, shipping_cost=shipping_cost, grand_total=grand_total)
    return redirect('myapp:my_cart')


class CheckoutView(BaseView):
    def post(self, request):
        template = render_to_string(
            'email/email_template.html', {'name': request.user.username})
        if request.method == 'POST':
            username = request.user.username
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            email = request.POST['email']
            shipping_add = request.POST['shipping_add']
            mobile_no = request.POST['mobile_no']
            zip_code = request.POST['zip_code']
            data = CheckoutCart.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                shipping_add=shipping_add,
                mobile_no=mobile_no,
                zip_code=zip_code,
            )
            data.save()
            send_email = EmailMessage(
                'Checkout completed',
                template,
                settings.EMAIL_HOST_USER,
                ['brunofernandez1001@gmail.com'],
                # [request.user.email],
                [email],
            )
            send_email.fail_silently = False
            send_email.send()
            Cart.objects.all().delete()
            CartTotal.objects.all().delete()
            CheckoutCart.objects.all().delete()
            messages.success(
                request, '✔ Checkout is done! Check your email to confirm!')
            return redirect("/")

    def get(self, request):
        user = request.user.username
        net_total = 0
        shipping_cost = 1000
        grand_total = 0
        self.views['cart_product'] = Cart.objects.filter(
            username=user, checkout=False, status='active')
        tots = CartTotal.objects.filter(username=user, checkout=False)
        for i in tots[:]:
            net_total = i.net_total
            shipping_cost = i.shipping_cost
            grand_total = i.grand_total
            date_checked = i.date_checked
        self.views['cart_total'] = [
            {'net_total': net_total, 'shipping_cost': shipping_cost, 'grand_total': grand_total, 'date_checked': date_checked}]
        return render(request, 'checkout.html', self.views)


# ------------------------API--------------------------


# managed from router
# ViewSets define the view behavior.
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializers


# needs a url to be managed
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializers
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filter_fields = ['id', 'category', 'label', 'brand']
    ordering_fields = ['id', 'price', 'name']
    search_fields = ['name', 'desc']
