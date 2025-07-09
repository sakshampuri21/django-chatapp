from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from ckeditor.fields import RichTextField

User=get_user_model()

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='')
    bio = RichTextField(blank=True, null=True)
    profileimg = models.ImageField(upload_to="images", default="images/defaultimage.jpeg")

    def __str__(self):
        return self.user.username


class Friend(models.Model):
    user = models.ForeignKey(User, related_name='friends', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friend_of', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'friend')

    def __str__(self):
        return f"{self.user.username} - {self.friend.username}"

    @classmethod
    def add_friend(cls, user1, user2):
        # Ensure that each friendship is unique and bidirectional
        friendship, created = cls.objects.get_or_create(user=user1, friend=user2)
        reverse_friendship, reverse_created = cls.objects.get_or_create(user=user2, friend=user1)
        return created or reverse_created  # Return True if either was newly created


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()  # Make sure this is 'content' if you reference it as such
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username}"

class Blocked(models.Model):
    blocker = models.ForeignKey(User, related_name='blocked_users', on_delete=models.CASCADE)
    blocked = models.ForeignKey(User, related_name='blocked_by', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)  # To track when the user was blocked

    class Meta:
        unique_together = ('blocker', 'blocked')  # Ensure each blocking relationship is unique

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"

    @classmethod
    def block_user(cls, blocker, blocked):
        # Block a user by creating an entry in the Blocked model
        blocked_relation, created = cls.objects.get_or_create(blocker=blocker, blocked=blocked)
        return created  # Return True if the block was newly created

    @classmethod
    def unblock_user(cls, blocker, blocked):
        # Unblock a user by deleting the entry in the Blocked model
        cls.objects.filter(blocker=blocker, blocked=blocked).delete()