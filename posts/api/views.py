from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings

from posts.api.permissions import IsOwnerOrReadOnly
from posts.api.serializers import ImageSerializer, NoteSerializer, NoteListSerializer

from posts.models import Note


class NoteListCreateAPIView(ListCreateAPIView):
    queryset = Note.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]  # Реагирует на (query) параметр `search`
    search_fields = ['@title', '@description']  # Используем полнотекстовый поиск Postgres
    ordering_fields = ["created_at", "mode_time", "user_username"]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NoteSerializer
        return NoteListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NoteDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    lookup_field = 'pk'
    lookup_url_kwarg = 'pk'
    permission_classes = [IsOwnerOrReadOnly]


class UploadImageAPIView(GenericAPIView):
    serializer_class = ImageSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        image: InMemoryUploadedFile = serializer.validated_data["image"]
        with open(f"{settings.MEDIA_ROOT}/images/{image.name}", "bw") as image_file:
            image_file.write(image.read())
        return Response({"name": image.name, "url": "images/" + image.name})
