from django.contrib import admin
from .models import Profile,Friend,Message,Blocked
# Register your models here.

admin.site.register(Profile)
admin.site.register(Friend)
admin.site.register(Message)
admin.site.register(Blocked)
