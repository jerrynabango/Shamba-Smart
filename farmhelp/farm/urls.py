from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('verify_otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('resend_otp/<int:user_id>/', views.resend_otp, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog_posts, name='blog_posts'),
    path('market/', views.market, name='market'),
    path('add_product', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product,
         name='edit_product'),
    path('delete_product/<int:product_id>/', views.delete_product,
         name='delete_product'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('add/', views.add_blog_post, name='add_blog_post'),
    path('blog/<int:post_id>/', views.post_detail, name='post_detail'),
    path('blog/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('blog/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('comment/<int:comment_id>/react/', views.comment_reaction,
         name='comment_reaction'),
    path('post/<int:post_id>/react/', views.post_reaction,
         name='post_reaction'),
    path('profile/<int:user_id>/', views.view_profile, name='view_profile'),
    path('password_reset/', auth_views.PasswordResetView.as_view(),
         name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
    path('send_message/<int:receiver_id>/', views.send_message_user,
         name='send_message_user'),
    path('message_sent/', views.message_sent, name='message_sent'),
    path('inbox/', views.inbox, name='inbox'),
    path('sent_messages/', views.sent_messages, name='sent_messages'),
    #path('message-deleted//<int:message_id>/', views.message_deleted, name='message_deleted'),
    path('edit/<int:message_id>/', views.edit_message, name='edit_message'),
    path('delete/<int:message_id>/', views.delete_message,
         name='delete_message'),
    path('reply/<int:message_id>/', views.reply_message,
         name='reply_message'),
    path('contact/', views.contact_us, name='contact_us'),
    path('place_order/<int:listing_id>/', views.place_order,
         name='place_order'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('process_payment/', views.process_payment, name='process_payment'),
]

# path('chat/<str:username>/', views.chat_view, name='chat_view'),
# path('send-message/', views.send_message_ajax, name='send_message_ajax'),
