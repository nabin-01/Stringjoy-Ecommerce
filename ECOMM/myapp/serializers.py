from django.contrib.auth.models import User
from django.urls import include, path
from rest_framework import serializers

from .models import *


# Serializers define the API representation.
class ProductSerializers(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        # fields = ['url', 'username', 'email', 'is_staff']
