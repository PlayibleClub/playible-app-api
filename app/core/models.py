from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
                                        PermissionsMixin
from django.conf import settings

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """Creates and saves a new user"""
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Creates and saves a new super user"""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that supports using email instead of username"""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

class BaseInfo(models.Model):
  created_at = models.DateTimeField(auto_now=False, auto_now_add=True, blank=True, null=True)
  updated_at = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)

  class Meta:
      ordering = ['-updated_at', '-created_at']
      abstract = True

class Account(BaseInfo):
  username = models.CharField(max_length=155)
  wallet_address = models.CharField(max_length=155, unique=True)
  image_url = models.CharField(max_length=155, null=True, blank=True)

  def __str__(self):
    return self.username
    
  class Meta:
    ordering = ['-created_at', '-updated_at']

class AssetContract(BaseInfo):
  athlete_id = models.ForeignKey("Athlete", on_delete=models.CASCADE)
  symbol = models.CharField(max_length=155, unique=True)
  name = models.CharField(max_length=155)
  contract_addr = models.CharField(max_length=155)
  
  def __str__(self):
    return self.name
    
  class Meta:
    ordering = ['-created_at', '-updated_at']

class Asset(BaseInfo):
  name = models.CharField(max_length=155)
  owner = models.ForeignKey("Account", on_delete=models.CASCADE)
  contract = models.ForeignKey("AssetContract", on_delete=models.CASCADE)
  image_url = models.CharField(max_length=155, null=True, blank=True)
  
  def __str__(self):
    return self.name
    
  class Meta:
    ordering = ['-created_at', '-updated_at']

class AssetProperties(BaseInfo):
  class DataType(models.TextChoices):
    NUMBER = 'NUMBER'
    STRING = 'STRING'
  name = models.CharField(max_length=155)
  value = models.CharField(max_length=155)
  data_type = models.CharField(max_length=30, choices=DataType.choices, default=DataType.STRING)

  def __str__(self):
    return self.name

  class Meta:
    ordering = ['-created_at', '-updated_at']

class Athlete(BaseInfo):
    name = models.CharField(max_length=155)
    terra_id = models.CharField(max_length=155)
    api_id = models.IntegerField()
    team = models.ForeignKey("Team", on_delete=models.CASCADE)
    positions = models.ManyToManyField('Positions')
    jersey = models.IntegerField()
    is_active = models.BooleanField()
    is_injured = models.BooleanField()
    is_suspended = models.BooleanField()

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at', '-updated_at']

class Positions(BaseInfo):
    name = models.CharField(max_length=155)
    abbreviation = models.CharField(max_length=2, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at', '-updated_at']

class Season(BaseInfo):
    name = models.CharField(max_length=155)
    season = models.IntegerField()
    is_active = models.BooleanField()

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at', '-updated_at']

class AthleteSeason(BaseInfo):
    athlete = models.ForeignKey("Athlete", on_delete=models.CASCADE)
    season = models.ForeignKey("Season", on_delete=models.CASCADE)
    fantasy_score = models.DecimalField(max_digits=19, decimal_places=10)
    points = models.DecimalField(max_digits=19, decimal_places=10)
    rebounds = models.DecimalField(max_digits=19, decimal_places=10)
    assists = models.DecimalField(max_digits=19, decimal_places=10)
    blocks = models.DecimalField(max_digits=19, decimal_places=10)
    turnovers = models.DecimalField(max_digits=19, decimal_places=10)
    
    class Meta:
        ordering = ['-created_at', '-updated_at']

class Team(BaseInfo):
    location = models.CharField(max_length=155)
    nickname = models.CharField(max_length=155)
    api_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.location + ' ' + self.nickname
    
    class Meta:
        ordering = ['-created_at', '-updated_at']
