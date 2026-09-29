from django.shortcuts import render,get_object_or_404,redirect
from .models import Product,Category,Order,Review,Wishlist
from django.contrib.auth import authenticate, login, logout 
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

def home(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    products = Product.objects.all()

    if query:
        products = Product.objects.filter(name__icontains=query)

    if category:
        products = products.filter(category__id=category)

    categories = Category.objects.all()    
    
    return render(request,'home.html',{'products':products,'categories':categories})

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    reviews = Review.objects.filter(product=product)

    if request.method == "POST" and request.user.is_authenticated:
        rating = request.POST['rating']
        comment = request.POST['comment']

        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )

        return redirect('product_detail', id=id)

    return render(request, 'product_detail.html', {
        'product': product,
        'reviews': reviews
    })

def add_to_cart(request, id):

    product = get_object_or_404(Product, id=id)

    cart = request.session.get('cart', {})

    id = str(id)

    if product.stock <= 0:
        return redirect('home')

    if id in cart:

        if cart[id] < product.stock:
            cart[id] += 1

    else:

        cart[id] = 1

    request.session['cart'] = cart

    return redirect('home')
    

def increase_quantity(request, id):
    cart = request.session.get('cart', {})

    id = str(id)

    if id in cart:
        cart[id] += 1

    request.session['cart'] = cart

    return redirect('cart')


def decrease_quantity(request, id):
    cart = request.session.get('cart', {})

    id = str(id)

    if id in cart:
        cart[id] -= 1

        if cart[id] <= 0:
            del cart[id]

    request.session['cart'] = cart

    return redirect('cart')    

def cart(request):
    cart=request.session.get('cart',{})
    products=Product.objects.filter(id__in=cart.keys())
    total=0
    for product in products:
        product.quantity = cart[str(product.id)]
        product.subtotal = product.price * product.quantity
        total += product.subtotal

        

    return render(request,'cart.html',{'products':products,'total':total})

def remove_from_cart(request, id):
    cart = request.session.get('cart', {})
    id = str(id)

    if id in cart:
        cart.remove(id)

    request.session['cart'] = cart

    return redirect('cart')

@login_required
def checkout(request):
    if request.method == 'POST':
        name = request.POST['name']
        address = request.POST['address']
        phone = request.POST['phone']
        cart = request.session.get('cart', {})

        for product_id, quantity in cart.items():

            product = Product.objects.get(id=product_id)

            if product.stock >= quantity:

                product.stock -= quantity
                product.save()


        Order.objects.create(
            user=request.user,
            name=name,
            address=address,
            phone=phone
        )

        request.session['cart'] = {}

        return render(request, 'success.html')

    return render(request, 'checkout.html')

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            user.set_password(user.password)
            user.save()

            login(request, user)

            return redirect('home')

    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('home')

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def order_history(request):
    orders = Order.objects.filter(
        user=request.user
    )

    return render(
        request,
        'order_history.html',
        {'orders': orders}
    )

@login_required
def add_to_wishlist(request, id):
    product = get_object_or_404(Product, id=id)

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect('home')


@login_required
def wishlist(request):
    items = Wishlist.objects.filter(user=request.user)

    return render(request, 'wishlist.html', {
        'items': items
    })

def download_invoice(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 18)
    p.drawString(180, 800, "MY E-COMMERCE STORE")

    p.setFont("Helvetica", 14)
    p.drawString(50, 760, "Invoice")

    p.setFont("Helvetica", 12)

    p.drawString(50, 720, "Customer Name : " + request.user.username)

    p.drawString(50, 700, "Thank you for shopping with us!")

    p.drawString(50, 680, "Visit Again!")

    p.showPage()
    p.save()

    return response

@login_required
def dashboard(request):

    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_users = User.objects.count()
    total_orders = Order.objects.count()

    total_revenue = Product.objects.aggregate(
        total=Sum('price')
    )['total'] or 0

    recent_orders = Order.objects.order_by('-id')[:5]

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    }

    return render(request, 'dashboard.html', context)
# Create your views here.
