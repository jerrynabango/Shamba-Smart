from django.contrib import admin
from .models import BlogPost, Comment, CustomUser, DirectMessage, MarketListing, OTP, CommentReaction, BlogPostReaction, Contact

admin.site.register(CustomUser)
admin.site.register(BlogPost)
admin.site.register(Comment)
admin.site.register(MarketListing)
admin.site.register(DirectMessage)
admin.site.register(CommentReaction)
admin.site.register(BlogPostReaction)
admin.site.register(OTP)
admin.site.register(Contact)
