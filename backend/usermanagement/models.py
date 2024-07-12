from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from .utils import random_filename

class CustomUserManager(BaseUserManager):
	def create_user(self, email, displayname, password=None, **extra_fields):
		if not email:
			raise ValueError('The Email field must be set')
		email = self.normalize_email(email)
		user = self.model(email=email, displayname=displayname, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, displayname, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)

		return self.create_user(email, displayname, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
	id = models.AutoField(primary_key=True)
	email = models.EmailField(unique=True)
	displayname = models.CharField(max_length=20)
	profile_picture = models.ImageField(upload_to=random_filename, default='default.png')
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)

	objects = CustomUserManager

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['displayname']

	def __str__(self):
		return self.email


class Games(models.Model):
	id = models.AutoField(primary_key=True)
	home_id = models.ForeignKey(CustomUser, related_name='home_id', on_delete=models.SET_NULL, null=True)
	visitor_id = models.ForeignKey(CustomUser, related_name='visitor_id', on_delete=models.SET_NULL, null=True)
	visitor_score = models.IntegerField()
	home_score = models.IntegerField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Game {self.id} Home: {self.home_id} Visitor: {self.visitor_id}"