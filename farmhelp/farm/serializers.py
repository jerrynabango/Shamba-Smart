from rest_framework import serializers
from .models import CustomUser, BlogPost, BlogPostReaction, Comment, CommentReaction, MarketListing, DirectMessage, OTP, Contact, Order


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'profile_picture',
                  'phone_number', 'bio', 'location', 'linkedin', 'x',
                  'facebook', 'whatsapp']


class BlogPostSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'content', 'author', 'created_at',
                  'updated_at', 'views', 'reactions']


class BlogPostReactionSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    blog_post = BlogPostSerializer(read_only=True)

    class Meta:
        model = BlogPostReaction
        fields = ['id', 'user', 'blog_post', 'reaction_type', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    post = BlogPostSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'post', 'created_at',
                  'updated_at', 'reactions']


class CommentReactionSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    comment = CommentSerializer(read_only=True)

    class Meta:
        model = CommentReaction
        fields = ['id', 'user', 'comment', 'reaction_type', 'created_at']


class MarketListingSerializer(serializers.ModelSerializer):
    farmer = CustomUserSerializer(read_only=True)

    class Meta:
        model = MarketListing
        fields = ['id', 'product_name', 'description', 'price', 'farmer',
                  'currency', 'status', 'created_at', 'updated_at', 'image']


class DirectMessageSerializer(serializers.ModelSerializer):
    sender = CustomUserSerializer(read_only=True)
    receiver = CustomUserSerializer(read_only=True)

    class Meta:
        model = DirectMessage
        fields = ['id', 'sender', 'receiver', 'message', 'timestamp']


class OTPSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = OTP
        fields = ['id', 'user', 'otp', 'created_at']


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'email', 'phone', 'message', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    product = MarketListingSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'product', 'user', 'quantity', 'name', 'location',
                  'phone_number', 'order_date', 'status']
