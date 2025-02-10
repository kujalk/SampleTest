# models.py
from django.db import models
import json
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError

class IPService(models.Model):
    service_name = models.CharField(max_length=100, unique=True)
    ip_addresses = models.TextField(default='[]')  # Stores JSON string of IP addresses
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.service_name

    def get_ip_list(self):
        try:
            return json.loads(self.ip_addresses)
        except json.JSONDecodeError:
            return []

    def set_ip_list(self, ip_list):
        # Validate IPs before saving
        for ip in ip_list:
            validate_ipv4_address(ip)
        self.ip_addresses = json.dumps(list(set(ip_list)))  # Remove duplicates

    def add_ip(self, ip):
        validate_ipv4_address(ip)
        ip_list = self.get_ip_list()
        if ip not in ip_list:
            ip_list.append(ip)
            self.ip_addresses = json.dumps(ip_list)
            return True
        return False

    def remove_ip(self, ip):
        ip_list = self.get_ip_list()
        if ip in ip_list:
            ip_list.remove(ip)
            self.ip_addresses = json.dumps(ip_list)
            return True
        return False

    class Meta:
        ordering = ['-updated_at']

# serializers.py
from rest_framework import serializers

class IPServiceSerializer(serializers.ModelSerializer):
    ip_addresses = serializers.ListField(
        child=serializers.CharField(validators=[validate_ipv4_address]),
        required=False
    )

    class Meta:
        model = IPService
        fields = ['service_name', 'ip_addresses', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['ip_addresses'] = instance.get_ip_list()
        return ret

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        if 'ip_addresses' in internal_value:
            internal_value['ip_addresses'] = json.dumps(internal_value['ip_addresses'])
        return internal_value

class IPAddressUpdateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['add', 'remove'])
    ip_address = serializers.CharField(validators=[validate_ipv4_address])

# views.py
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response

class IPServiceCreateView(generics.CreateAPIView):
    queryset = IPService.objects.all()
    serializer_class = IPServiceSerializer

class IPServiceRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = IPService.objects.all()
    serializer_class = IPServiceSerializer
    lookup_field = 'service_name'

    def update_ip_address(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = IPAddressUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            ip_address = serializer.validated_data['ip_address']
            
            if action == 'add':
                if instance.add_ip(ip_address):
                    instance.save()
                    return Response({'message': f'IP {ip_address} added successfully'})
                return Response(
                    {'message': 'IP already exists'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            elif action == 'remove':
                if instance.remove_ip(ip_address):
                    instance.save()
                    return Response({'message': f'IP {ip_address} removed successfully'})
                return Response(
                    {'message': 'IP not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        return self.update_ip_address(request, *args, **kwargs)

# urls.py
from django.urls import path

urlpatterns = [
    path('api/ip-services/', IPServiceCreateView.as_view(), name='ipservice-create'),
    path('api/ip-services/<str:service_name>/', IPServiceRetrieveUpdateDestroyView.as_view(), name='ipservice-detail'),
]
















######################
Key changes made:

Replaced ModelViewSet with separate views:

IPServiceCreateView for creating new services
IPServiceRetrieveUpdateDestroyView for retrieve/update/delete operations


Changed lookup field to service_name instead of id
Updated URLs to use service_name in the path

You can now use the API like this:
pythonCopy# Create a new service
POST /api/ip-services/
{
    "service_name": "my_service",
    "ip_addresses": ["192.168.1.1", "192.168.1.2"]
}

# Retrieve a service
GET /api/ip-services/my_service/

# Update a service
PUT /api/ip-services/my_service/
{
    "service_name": "my_service",
    "ip_addresses": ["192.168.1.1", "192.168.1.3"]
}

# Add/remove IP
POST /api/ip-services/my_service/
{
    "action": "add",
    "ip_address": "192.168.1.4"
}

# Delete a service
DELETE /api/ip-services/my_service/

#######################
