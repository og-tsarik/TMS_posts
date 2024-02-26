from django.contrib.auth import get_user_model
from rest_framework import serializers

from posts.models import Note, Tag


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email', 'phone']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class ImageSerializer(serializers.Serializer):
    image = serializers.ImageField(write_only=True)

    class Meta:
        fields = ["image"]


class NoteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Note
        fields = ["uuid", "title", "content", "created_at", "mod_time", "image", "user", "tags"]
        read_only_fields = ["uuid", "user", "created_at", "mod_time"]
        write_only_fields = ["title", "content", "image", "tags"]

    def create(self, validated_data) -> Note:
        tags = validated_data.pop("tags")

        note = Note.objects.create(**validated_data)

        tags_objects: list[Tag] = []

        for tag in tags:
            obj, created = Tag.objects.get_or_create(name=tag["name"])
            tags_objects.append(obj)

        note.tags.set(tags_objects)

        return note


class NoteListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Note
        fields = ["uuid", "title", "content", "created_at", "mod_time", "image", "user", "tags"]


class NoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["title", "content", "created_at", "mod_time", "image", "tags"]


class NoteDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["uuid", "title", "content", "created_at", "mod_time", "image", "user", "tags"]
