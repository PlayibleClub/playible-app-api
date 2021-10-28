from django.db import models
from core.models import BaseInfo


class Account(BaseInfo):
    username = models.CharField(max_length=155)
    wallet_addr = models.CharField(max_length=155, unique=True)
    image_url = models.CharField(max_length=155, null=True, blank=True)

    def __str__(self):
        return self.username
        
    class Meta:
        ordering = ['-created_at', '-updated_at']


class AssetContract(BaseInfo):
    athlete_id = models.ForeignKey("fantasy.Athlete", on_delete=models.CASCADE)
    symbol = models.CharField(max_length=155, unique=True)
    name = models.CharField(max_length=155)
    contract_addr = models.CharField(max_length=155)
    
    def __str__(self):
        return self.name
        
    class Meta:
        ordering = ['-created_at', '-updated_at']


class Asset(BaseInfo):
    name = models.CharField(max_length=155) #Token ID
    owner = models.ForeignKey("Account", on_delete=models.CASCADE)
    contract = models.ForeignKey("AssetContract", on_delete=models.CASCADE)
    image_url = models.CharField(max_length=155, null=True, blank=True)
    
    def __str__(self):
        return self.name
      
    class Meta:
        ordering = ['-created_at', '-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['name','contract'], name='unique_position'),
        ]


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


class PrelaunchEmail(BaseInfo):
    email = models.EmailField(max_length=255, unique=True)

    def __str__(self):
        return self.email
    
    class Meta:
        ordering = ['-created_at', '-updated_at']
