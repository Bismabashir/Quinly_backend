from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework_simplejwt.tokens import AccessToken
from django.utils.timezone import now
from datetime import timedelta

User = get_user_model()


class CustomSerializer(serializers.Serializer):

    def run_validation(self, data):
        try:
            return super().run_validation(data)
        except serializers.ValidationError as exc:
            errors = []
            for field, messages in exc.detail.items():
                errors.append(" ".join(messages))
            raise serializers.ValidationError({"message": " ".join(errors)})

    def to_representation(self, instance):
        if isinstance(instance, dict) and "non_field_errors" in instance:
            return {"message": instance["non_field_errors"][0]}
        return instance


class RegisterSerializer(CustomSerializer):
    full_name = serializers.CharField(error_messages={"required": "Full name is required."})
    email = serializers.EmailField(error_messages={"required": "Email is required."})
    password = serializers.CharField(write_only=True, error_messages={"required": "Password is required."})

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(CustomSerializer):
    email = serializers.EmailField(error_messages={"required": "Email is required."})
    password = serializers.CharField(write_only=True, error_messages={"required": "Password is required."})

    def validate(self, data):
        user = User.objects.filter(email=data["email"]).first()

        if user is None or not user.check_password(data["password"]):
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("Your account is inactive. Please contact support.")

        access_token = AccessToken.for_user(user)
        access_token.set_exp(from_time=now() + timedelta(days=7))
        return {
            "access": str(access_token),
            "expires_in": access_token.payload["exp"],
            "user": UserSerializer(user).data
        }


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', "is_active", "is_superuser", 'created_at', 'updated_at']


class ForgotPasswordSerializer(CustomSerializer):
    email = serializers.EmailField(error_messages={"required": "Email is required."})

    def validate_email(self, value):
        user = User.objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError("No user found with this email.")
        return value


class ResetPasswordSerializer(CustomSerializer):
    email = serializers.EmailField(error_messages={"required": "Email is required."})
    new_password = serializers.CharField(write_only=True, min_length=8, error_messages={
        "required": "New password is required.",
        "min_length": "Password must be at least 8 characters long."
    })
    confirm_password = serializers.CharField(write_only=True,
                                             error_messages={"required": "Confirm password is required."})

    def validate(self, data):
        email = data.get("email")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"email": "No user found with this email."})

        data["user"] = user
        return data

    def save(self):
        user = self.validated_data["user"]
        new_password = self.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        return {"success": True}
