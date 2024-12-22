from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings


# Create your models here.
# User
class CustomUser(AbstractUser):
    FARMER = 'Farmer'
    PROFESSIONAL = 'Professional'

    ROLE_CHOICES = [
        (FARMER, 'Farmer'),
        (PROFESSIONAL, 'Professional'),
    ]

    role = models.CharField(max_length=50, choices=ROLE_CHOICES,
                            default=FARMER)
    profile_picture = models.ImageField(
        default='images/default_profile.png',
        upload_to='profile_pics/',
        null=True,
        blank=True
    )
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    linkedin = models.URLField(null=True, blank=True)
    x = models.URLField(null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    whatsapp = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.username


# Reactions
REACTION_CHOICES = [
    ('like', 'Like'),
    ('dislike', 'Dislike'),
    ('love', 'Love'),
]


# BlogPost
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    reactions = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def increase_views(self):
        self.views += 1
        self.save()

    def increase_reactions(self):
        self.reactions += 1
        self.save()


# Blog Reaction Choices
class BlogPostReaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)


# Comment
class Comment(models.Model):
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reactions = models.PositiveIntegerField(default=0)

    user_reactions = models.ManyToManyField(
        CustomUser,
        through='CommentReaction',
        related_name='comment_reactions'
    )

    def __str__(self):
        return self.content


# Comments Reaction Choices
class CommentReaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)


# Market List
class MarketListing(models.Model):
    product_name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                               related_name="products")
    currency = models.CharField(
        max_length=3,
        choices=[('USD', 'USD'), ('KES', 'KES'), ('EUR', 'EUR')],
        default='KES'
    )
    status = models.CharField(
        max_length=50,
        choices=[('Available', 'Available'), ('Sold', 'Sold')],
        default='Available'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='product_images/', null=True,
                              blank=True)

    def __str__(self):
        return self.product_name


# Direct Message
class DirectMessage(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                               related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                 related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"


# Signal for DirectMessage creation
@receiver(post_save, sender=DirectMessage)
def notify_user_on_new_message(sender, instance, created, **kwargs):
    if created:
        print(f"New message sent from {instance.sender} to {instance.receiver}")


# OTP
class OTP(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)


# Contact Us
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


# Order
class Order(models.Model):
    product = models.ForeignKey(MarketListing, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    order_date = models.DateTimeField(default=timezone.now)
    status_choices = [
        ('Pending Payment', 'Pending Payment'),
        ('Payment Successful', 'Payment Successful'),
        ('Payment Failed', 'Payment Failed'),
    ]
    order_status = models.CharField(max_length=20, choices=status_choices,
                                    default='Pending Payment')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.product.title}"


# Mpesa Payment
class TransactionLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    response_code = models.CharField(max_length=5)
    response_description = models.TextField()
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
