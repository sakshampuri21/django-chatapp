import json
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Message, Friend, Blocked


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        self.friend_id = self.scope["url_route"]["kwargs"]["friend_id"]

        if not self.user.is_authenticated:
            await self.close()
            return

        if not await self.can_chat():
            await self.close()
            return

        a, b = sorted([self.user.id, self.friend_id])
        self.group = f"chat_{a}_{b}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        try:
            content = json.loads(text_data).get("content", "").strip()
            if not content:
                return
            msg = await self.save_message(content)

            # 1) live message inside the open chat (both users if they are in it)
            await self.channel_layer.group_send(self.group, {
                "type": "chat_message",
                "id": msg["id"],
                "content": msg["content"],
                "sender_id": self.user.id,
                "sender": self.user.username,
                "time": msg["time"],
            })

            # 2) notify the recipient's index page (dot + preview)
            await self.channel_layer.group_send(f"user_{self.friend_id}", {
                "type": "notify",
                "from_id": self.user.id,
                "content": msg["content"],
                "time": msg["time"],
                "mine": False,
            })

            # 3) update the sender's own index page preview (other tabs)
            await self.channel_layer.group_send(f"user_{self.user.id}", {
                "type": "notify",
                "from_id": self.friend_id,
                "content": msg["content"],
                "time": msg["time"],
                "mine": True,
            })
        except Exception:
            traceback.print_exc()

    async def chat_message(self, event):
        try:
            if event["sender_id"] != self.user.id:
                await self.mark_read(event["id"])
            await self.send(text_data=json.dumps(event))
        except Exception:
            traceback.print_exc()

    @database_sync_to_async
    def can_chat(self):
        if not User.objects.filter(id=self.friend_id).exists():
            return False
        if not Friend.objects.filter(user=self.user, friend_id=self.friend_id).exists():
            return False
        if Blocked.objects.filter(blocker=self.user, blocked_id=self.friend_id).exists():
            return False
        if Blocked.objects.filter(blocker_id=self.friend_id, blocked=self.user).exists():
            return False
        return True

    @database_sync_to_async
    def save_message(self, content):
        m = Message.objects.create(
            sender=self.user, recipient_id=self.friend_id, content=content)
        return {
            "id": m.id,
            "content": m.content,
            "time": timezone.localtime(m.timestamp).strftime("%H:%M, %d %b %Y"),
        }

    @database_sync_to_async
    def mark_read(self, message_id):
        Message.objects.filter(id=message_id).update(is_read=True)


class NotifyConsumer(AsyncWebsocketConsumer):
    """One per logged-in user on the index page. Receives 'new message' notifications."""

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        self.group = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def notify(self, event):
        await self.send(text_data=json.dumps(event))