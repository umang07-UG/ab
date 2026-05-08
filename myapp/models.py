from django.db import models


class User(models.Model):
    name          = models.CharField(max_length=100)
    email         = models.EmailField(unique=True)
    mobile        = models.BigIntegerField(default=0, blank=True, null=True)
    password      = models.CharField(max_length=100)
    profile_image = models.ImageField(default='', upload_to='profile_img/', blank=True)

    def __str__(self):
        return self.name


class Chat(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user2')

    def __str__(self):
        return f"{self.user1} - {self.user2}"


class Message(models.Model):
    sender   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    text      = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read   = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.text[:30]}"
