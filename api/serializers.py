from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import Exercise, User, Workout


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        """
        Ensures the username is unique (case-insensitive) and stores it in lowercase.
        """
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value.lower()
        
    def create(self, validated_data):
        """
        Validates the password according to Django's password rules
        Hashes the password before saving the user to the database.
        """
        password = validated_data.pop("password")
        user = User(**validated_data)
        try:
            validate_password(password, user)
        except ValidationError as err:
            raise serializers.ValidationError({'password': err.messages})
        user.set_password(password)
        user.save()
        return user


class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = ['id', 'name', 'owner']
        extra_kwargs = {'owner': {'read_only': True}}


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'sets', 'reps', 'weight']
    
    def update(self, instance, validated_data):
        """
        Only the 'weight' field is allowed to be updated.
        Attempting to update any other field will raise a ValidationError.
        """
        allowed = {'weight', 'reps'}
        forbidden = set(validated_data) - allowed
        if forbidden:
            raise serializers.ValidationError(
                {field: "This field cannot be updated." for field in forbidden}
            )
        for field in allowed:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance


class ProteinSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['protein_goal', 'todays_protein']
        extra_kwargs = {'todays_protein': {'read_only': True}}