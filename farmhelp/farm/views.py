from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.conf import settings
from .models import BlogPost, MarketListing, CustomUser, DirectMessage, Comment, BlogPostReaction, CommentReaction, OTP, Contact, Order, TransactionLog
from django.contrib.auth.decorators import login_required
from django_otp import user_has_device
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
from .forms import CommentForm, ProfileEditForm, BlogPostForm, MarketListingForm, DirectMessageForm, CustomUserCreationForm, OrderForm
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.utils import timezone
from asgiref.sync import async_to_sync
import random
import string
import logging
import requests
from channels.layers import get_channel_layer
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import base64
import json
from decouple import config


logger = logging.getLogger(__name__)


# Generate OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


# Registration
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Generate OTP
            otp = generate_otp()
            OTP.objects.create(user=user, otp=otp)
            # Send OTP to email
            send_mail(
                'Your OTP Code',
                f'Your OTP code is: {otp}. It is valid for 10 minutes.',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            return redirect('verify_otp', user_id=user.id)
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


# OTP Verification
def verify_otp(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    otp_record = OTP.objects.get(user=user)

    if request.method == 'POST':
        otp = request.POST.get('otp')

        if otp == otp_record.otp:
            if otp_record.is_expired():
                messages.error(request, 'The OTP has expired. Please request a new one.')
            else:
                user.is_active = True
                user.save()
                messages.success(request, 'Your account has been activated. Please log in now.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'verify_otp.html', {'user': user,
                                               'otp_record': otp_record})


# Resend OTP
def resend_otp(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    otp_record = OTP.objects.get(user=user)

    if otp_record.is_expired():
        otp = generate_otp()
        otp_record.otp = otp
        otp_record.created_at = timezone.now()
        otp_record.save()
        send_mail(
            'Your OTP Code',
            f'Your new OTP code is: {otp}. It is valid for 10 minutes.',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        messages.success(request, 'A new OTP has been sent to your email.')
    else:
        messages.info(request, 'Your OTP is still valid.')

    return redirect('verify_otp', user_id=user.id)


# Login User
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


# Logout User
def logout_view(request):
    logout(request)
    return redirect('home')


# Home
def home(request):
    return render(request, 'home.html')


# Blogs
@login_required
def blog_posts(request):
    posts = BlogPost.objects.all()
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    logger.info(f"Pagination: Page {page_number}, Total Pages {paginator.num_pages}")
    return render(request, 'blog.html', {'posts': posts})


# Post Details
@login_required
def post_detail(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    post.increase_views()  # Increase view count
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post_detail', post_id=post.id)
    else:
        comment_form = CommentForm()
    return render(request, 'post_detail.html', {'post': post,
                                                'comment_form': comment_form})


# Post Reaction
@login_required
def post_reaction(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    reaction_type = request.POST.get('reaction_type')

    existing_reaction = BlogPostReaction.objects.filter(user=request.user,
                                                        blog_post=post).first()

    if existing_reaction:
        existing_reaction.reaction_type = reaction_type
        existing_reaction.save()
    else:
        BlogPostReaction.objects.create(user=request.user, blog_post=post,
                                        reaction_type=reaction_type)

    post.increase_reactions()
    return JsonResponse({'reactions': post.reactions})


# React to a Comment
@login_required
def comment_reaction(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    reaction_type = request.POST.get('reaction_type')

    existing_reaction = CommentReaction.objects.filter(user=request.user,
                                                       comment=comment).first()

    if existing_reaction:
        existing_reaction.reaction_type = reaction_type
        existing_reaction.save()
    else:
        CommentReaction.objects.create(user=request.user, comment=comment,
                                       reaction_type=reaction_type)
    comment.reactions += 1  # Increment the reaction count
    comment.save()
    return JsonResponse({'reactions': comment.reactions})


# Add Post
@login_required
def add_blog_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog_posts')
    else:
        form = BlogPostForm()

    return render(request, 'add_blog_post.html', {'form': form})


# Edit Post
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)

    if request.user != post.author and not request.user.is_staff:
        return redirect('post_detail', post_id=post.id)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_detail', post_id=post.id)
    else:
        form = BlogPostForm(instance=post)

    return render(request, 'edit_post.html', {'form': form, 'post': post})


# Delete Product
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    if request.user == post.author:
        post.delete()
        messages.success(request, "Post deleted successfully!")
    else:
        messages.error(request, "You are not authorized to delete this post.")
    return redirect('blog_posts')


# View other User's Profile
@login_required
def view_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'profile_view.html', {'user': user})


# User's Profile
@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})


# User Edit Profile
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES,
                               instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})


# Market Listings
@login_required
def market(request):
    listings = MarketListing.objects.filter(status='Available')
    return render(request, 'market.html', {'listings': listings})


# Add Product
@login_required
def add_product(request):
    if request.method == "POST":
        form = MarketListingForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.farmer = request.user
            form.save()
            return redirect('market')
    else:
        form = MarketListingForm()

    return render(request, 'add_product.html', {'form': form})


# Edit Product
@login_required
def edit_product(request, product_id):
    listing = get_object_or_404(MarketListing, id=product_id)

    if listing.farmer != request.user:
        return redirect('market')

    if request.method == "POST":
        form = MarketListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            form.save()
            return redirect('market')
    else:
        form = MarketListingForm(instance=listing)

    return render(request, 'edit_product.html', {'form': form})


# Delete Product
@login_required
def delete_product(request, product_id):
    listing = get_object_or_404(MarketListing, id=product_id)

    if listing.farmer != request.user:
        return redirect('market')

    listing.delete()
    return redirect('market')


# Direct Message
@login_required
def send_message_user(request, receiver_id):
    receiver = get_object_or_404(CustomUser, id=receiver_id)
    next_url = request.GET.get('next', 'market')

    if request.method == 'POST':
        form = DirectMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = receiver
            message.save()
            return redirect(next_url)
    else:
        form = DirectMessageForm(initial={'receiver': receiver})

    return render(request, 'send_message.html', {'form': form, 'receiver': receiver})



@login_required
def message_sent(request):
    return render(request, 'message_sent.html')


# Edit  message
@login_required
def edit_message(request, message_id):
    message = get_object_or_404(DirectMessage, id=message_id)

    if message.sender != request.user:
        return redirect('inbox')

    if request.method == 'POST':
        form = DirectMessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            return redirect('sent_messages')
    else:
        form = DirectMessageForm(instance=message)

    return render(request, 'edit_message.html', {'form': form,
                                                 'message': message})


# Inbox Message
@login_required
def inbox(request):
    received_messages = DirectMessage.objects.filter(receiver=request.user)
    return render(request, 'inbox.html', {'messages': received_messages})


# Sent Message
@login_required
def sent_messages(request):
    sent_messages = DirectMessage.objects.filter(sender=request.user)
    return render(request, 'sent_message.html', {'messages': sent_messages})

# Delete messages
# @login_required
# def message_deleted(request, message_id):
    #return render(request, 'message_deleted.html')


# Delete Message
@login_required
def delete_message(request, message_id):
    message = get_object_or_404(DirectMessage, id=message_id)
    if message.sender == request.user:
        current_page = 'sent_messages'
    elif message.receiver == request.user:
        current_page = 'inbox'
    else:
        return redirect('permission_denied')

    message.delete()
    return redirect(current_page)

# Reply message
@login_required
def reply_message(request, message_id):
    original_message = get_object_or_404(DirectMessage, id=message_id)

    if request.method == 'POST':
        form = DirectMessageForm(request.POST)
        if form.is_valid():
            new_message = form.save(commit=False)
            new_message.sender = request.user
            new_message.receiver = original_message.sender
            new_message.save()
            return redirect('inbox')
    else:
        form = DirectMessageForm()

    return render(request, 'reply_message.html', {'form': form,
                                                  'original_message': original_message})

# about
@login_required(login_url='/login_view/') 
def about(request):
    return render(request, 'about.html')


# Contact
def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        print(f"Form Data: Name={name}, Email={email}, Phone={phone}, Message={message}")

        contact = Contact.objects.create(
            name=name,
            email=email,
            phone=phone,
            message=message,
        )

        print(f"Contact Saved: {contact}")

        payload = {
            "name": name,
            "email": email,
            "phone": phone,
            "message": message,
        }

        try:
            formspree_url = "https://formspree.io/f/xeoqpvoo"
            headers = {"Accept": "application/json"}
            response = requests.post(formspree_url, data=payload, headers=headers)

            if response.status_code == 200:
                return render(request, 'contact.html', {'success_message': 'Message sent successfully!'})
            else:
                return render(request, 'contact.html', {'error_message': 'Failed to send your message. Please try again.'})

        except Exception as e:
            print(f"Error: {e}")
            return render(request, 'contact.html', {'error_message': 'An error occurred. Please check your connection.'})

    return render(request, 'contact.html')


@login_required
def place_order(request, listing_id):
    listing = get_object_or_404(MarketListing, id=listing_id)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.product = listing
            order.user = request.user
            order.order_status = 'Pending Payment'
            order.save()

            # Initiate M-Pesa Payment
            phone_number = form.cleaned_data['phone_number']
            amount = listing.price
            try:
                response = initiate_mpesa_payment(phone_number, amount)
                response_code = response.get('ResponseCode', 'Unknown')
                response_description = response.get('ResponseDescription', 'No description provided')

                # Log transaction
                TransactionLog.objects.create(
                    order=order,
                    response_code=response_code,
                    response_description=response_description,
                    transaction_id=response.get('CheckoutRequestID', None),
                )

                if response_code == '0':
                    return JsonResponse({'success': True, 'message': 'Payment initiated. Please enter your PIN.'})
                else:
                    order.order_status = 'Payment Failed'
                    order.save()
                    return JsonResponse({'success': False, 'message': response_description})
            except Exception as e:
                order.order_status = 'Payment Failed'
                order.save()
                TransactionLog.objects.create(
                    order=order,
                    response_code='500',
                    response_description=str(e),
                )
                return JsonResponse({'success': False, 'message': 'An error occurred while processing payment. Try again later.'})

        else:
            return JsonResponse({'success': False, 'message': 'Invalid form submission.'}, status=400)

    form = OrderForm()
    return render(request, 'place_order.html', {'listing': listing, 'form': form})


@csrf_exempt
def process_payment(request):
    """
    Processes the payment for an order.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            quantity = data.get('quantity')
            name = data.get('name')
            listing_id = data.get('listing_id')

            if not all([phone_number, quantity, name, listing_id]):
                return JsonResponse({'success': False, 'message': 'Missing required fields.'}, status=400)

            # Retrieve listing and calculate amount
            listing = MarketListing.objects.get(id=listing_id)
            amount = listing.price * int(quantity)

            # Initiate M-Pesa payment
            response = initiate_mpesa_payment(phone_number, amount)
            response_code = response.get('ResponseCode', 'Unknown')
            response_description = response.get('ResponseDescription', 'No description provided')

            # Log transaction
            TransactionLog.objects.create(
                response_code=response_code,
                response_description=response_description,
                transaction_id=response.get('CheckoutRequestID', None),
            )

            if response_code == '0':
                return JsonResponse({'success': True, 'message': 'Payment initiated. Please check your phone to enter your PIN.'})
            else:
                return JsonResponse({'success': False, 'message': response_description})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


def initiate_mpesa_payment(phone_number, amount):
    """
    Initiates the M-Pesa STK Push request.
    """
    try:
        # Load credentials from environment variables
        consumer_key = config('MPESA_CONSUMER_KEY')
        consumer_secret = config('MPESA_CONSUMER_SECRET')
        shortcode = config('MPESA_SHORTCODE')
        passkey = config('MPESA_PASSKEY')
        callback_url = config('MPESA_CALLBACK_URL')

        # Generate access token
        token_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        token_response = requests.get(token_url, auth=(consumer_key,
                                                       consumer_secret))
        if token_response.status_code != 200:
            raise Exception("Failed to authenticate with M-Pesa. Check credentials.")

        access_token = token_response.json().get('access_token')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()

        # Prepare STK Push request
        headers = {'Authorization': f'Bearer {access_token}'}
        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": "OrderPayment",
            "TransactionDesc": "Payment for Order",
        }

        response = requests.post('https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest', headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        raise Exception(f"M-Pesa request failed: {str(e)}")



@csrf_exempt
def mpesa_callback(request):
    """
    Handles M-Pesa payment callback.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        result_code = data['Body']['stkCallback']['ResultCode']
        checkout_request_id = data['Body']['stkCallback']['CheckoutRequestID']

        # Update order and log transaction
        transaction = TransactionLog.objects.get(transaction_id=checkout_request_id)
        order = transaction.order

        if result_code == 0:
            order.order_status = 'Payment Successful'
            transaction.response_description = 'Payment successful!'
        else:
            order.order_status = 'Payment Failed'
            transaction.response_description = 'Payment failed or cancelled.'

        order.save()
        transaction.save()

        return JsonResponse({'success': result_code == 0, 'message': transaction.response_description})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f"Callback processing error: {str(e)}"}, status=500)
