from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Follow


class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.ReadOnlyField()
    following_count = serializers.ReadOnlyField()
    is_following = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'bio', 'avatar', 'avatar_url', 'cover_image', 'cover_image_url',
            'is_artist', 'favorite_genres', 'followers_count', 'following_count',
            'is_following', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {'avatar': {'write_only': True}, 'cover_image': {'write_only': True}}

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=obj).exists()
        return False

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        # Bảo mật PII: Chỉ hiển thị email cho chính chủ tài khoản hoặc quản trị viên (staff)
        if not (request and request.user.is_authenticated and (request.user == instance or request.user.is_staff)):
            ret.pop('email', None)
        return ret



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'is_artist']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Mật khẩu xác nhận không khớp.'})

        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()

        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError({'username': 'Tên đăng nhập này đã được sử dụng.'})

        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({'email': 'Địa chỉ email này đã được sử dụng.'})

        data['username'] = username
        data['email'] = email
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        identifier = data.get('username', '').strip()
        password = data.get('password', '')

        if not identifier or not password:
            raise serializers.ValidationError('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.')

        user = None

        # 1. Try standard Django authenticate (exact username match)
        user = authenticate(username=identifier, password=password)

        # 2. Try email match if identifier has '@' or standard authenticate failed
        if not user and '@' in identifier:
            users_by_email = User.objects.filter(email__iexact=identifier).order_by('-id')
            for candidate in users_by_email:
                if candidate.check_password(password):
                    user = candidate
                    break

        # 3. Try case-insensitive username match
        if not user:
            users_by_username = User.objects.filter(username__iexact=identifier).order_by('-id')
            for candidate in users_by_username:
                if candidate.check_password(password):
                    user = candidate
                    break

        # 4. Fallback: check email even without '@'
        if not user:
            users_by_email = User.objects.filter(email__iexact=identifier).order_by('-id')
            for candidate in users_by_email:
                if candidate.check_password(password):
                    user = candidate
                    break

        if not user:
            raise serializers.ValidationError('Tên đăng nhập hoặc mật khẩu không đúng.')
        if not user.is_active:
            raise serializers.ValidationError('Tài khoản đã bị vô hiệu hóa.')

        data['user'] = user
        return data


class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
