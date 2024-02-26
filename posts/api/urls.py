from django.urls import path

from . import views

# /api/posts/
app_name = 'posts:api'

urlpatterns = [

    path("", views.NoteListCreateAPIView.as_view(), name="note-list-create"),
    path("<uuid:pk>", views.NoteDetailAPIView.as_view(), name="note"),
    path("image", views.UploadImageAPIView.as_view(), name="note-image-upload")
]
