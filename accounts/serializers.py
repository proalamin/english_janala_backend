from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone', 'institute']


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='first_name', read_only=True)
    phone = serializers.SerializerMethodField()
    institute = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'phone', 'institute', 'is_staff']

    def get_phone(self, obj):
        return getattr(getattr(obj, 'profile', None), 'phone', '')

    def get_institute(self, obj):
        return getattr(getattr(obj, 'profile', None), 'institute', '')


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, max_length=150)
    phone = serializers.CharField(write_only=True, max_length=20, required=False, allow_blank=True)
    institute = serializers.CharField(write_only=True, max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'institute', 'password']

    def validate_email(self, value):
        email = value.strip().lower()
        if not email:
            raise serializers.ValidationError('Email is required.')
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return email

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data):
        name = validated_data.pop('name').strip()
        phone = validated_data.pop('phone', '').strip()
        institute = validated_data.pop('institute', '').strip()
        email = validated_data['email']
        password = validated_data.pop('password')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
        )
        Profile.objects.create(user=user, phone=phone, institute=institute)
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Accepts {email, password} and authenticates against the default
    username-based backend by resolving email -> username first."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = serializers.EmailField()
        if self.username_field in self.fields and self.username_field != 'email':
            del self.fields[self.username_field]

    def validate(self, attrs):
        email = (attrs.get('email') or '').strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError({'detail': 'Invalid email or password.'}) from exc

        attrs[self.username_field] = user.username
        data = super().validate(attrs)
        data['user'] = UserSerializer(user).data
        return data
