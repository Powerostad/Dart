from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile, SubscriptionPlan, CustomUser
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from django.contrib.auth.models import User
from django.conf import settings

User = get_user_model()

class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for handling CRUD on the User model"""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'profile_picture_url', 'bio',
            'created_at', 'updated_at'
        ]


class UserLoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class UserLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class UserRegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    referral_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
        'id', 'username', 'email', 'plan', 'password1', 'password2', 'created_at', 'updated_at', 'referral_code',
        "phone_number",)
        read_only_fields = ('id', 'plan', 'created_at', 'updated_at')

    def validate(self, attrs):
        # Check if passwords match
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Validate referral code, if provided
        referral_code = attrs.get('referral_code')
        if referral_code and not User.objects.filter(referral_code=referral_code).exists():
            raise serializers.ValidationError({"referred_by": _("Invalid referral code.")})

        return attrs

    def create(self, validated_data):
        # Extract passwords
        password = validated_data.pop('password1')
        validated_data.pop('password2')

        # Extract referral code
        referral_code = validated_data.pop('referral_code', None)

        # Create user
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Handle referral code logic
        if referral_code:
            try:
                referring_user = User.objects.get(referral_code=referral_code)
                referring_user.profile.points += 10
                referring_user.profile.save()
            except User.DoesNotExist:
                raise serializers.ValidationError({"referral_code": _("Invalid referral code.")})

        return user


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class EmailRequestSerializer(serializers.Serializer):
    to_email = serializers.EmailField()
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
    
    
class UserAdminCreationSerializer(serializers.Serializer):
    api_password = serializers.CharField(write_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_api_password(self, value):
        if value != settings.API_SECRET:
            raise AuthenticationFailed("Invalid API password.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise ValidationError("A user with this username already exists.")
        return value

    def validate(self, attrs):
        required_fields = ["username", "email", "password", "api_password"]
        missing_fields = [field for field in required_fields if not attrs.get(field)]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        return attrs

    def create(self, validated_data):
        username = validated_data["username"]
        email = validated_data["email"]
        password = validated_data["password"]

        # Create user with admin privileges
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()

        return user    
    
