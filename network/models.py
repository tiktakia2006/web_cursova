from django.db import models
from django.contrib.auth.models import User


class Route(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routes')
    start_location = models.CharField(max_length=255)
    end_location = models.CharField(max_length=255, default='')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='routes_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.start_location} - {self.end_location}"


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    friends = models.ManyToManyField(User, related_name='friends_profiles', blank=True)
    def __str__(self):
        return self.user.username


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    caption = models.TextField()
    image = models.ImageField(upload_to='posts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    def __str__(self):
        return self.caption

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    route = models.ForeignKey(Route, related_name='comments', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

