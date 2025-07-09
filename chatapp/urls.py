from django.urls import path
from .import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login,name="login"),
    path('logout/', views.logout,name="logout"),
    path('index/', views.index,name="index"),
    path('settings/', views.settings,name="settings"),
    path('settings/profile/', views.profile_settings, name='profile_settings'),
    path('settings/profile/update/', views.update_profile, name='update_profile'),
    path('settings/account/', views.account_settings, name='account_settings'),
    path('delete_account/', views.delete_account,name="delete_account"),
    path('search/', views.search_friends, name='search_friends'),
    path('add_friend/', views.add_friend, name='add_friend'),
    path('send-message/<int:friend_id>/', views.send_message, name='send_message'),
    # path('delete_message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('remove_friend/<int:friend_id>/', views.remove_friend, name='remove_friend'), 
    path('view-profile/<int:pk>/', views.view_profile, name='view_profile'), 
    path('block_friend/<int:friend_id>/', views.block_friend, name='block_friend'),
    path('unblock_friend/<int:friend_id>/', views.unblock_friend, name='unblock_friend'),
]