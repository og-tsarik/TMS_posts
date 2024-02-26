from django.contrib import admin
from django.db.models import QuerySet, F
from django.db.models.functions import Upper
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .models import Note, Tag, User


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    #  list_editable = ["title"], !но тогда не должен быть первым в "list_display"!
    # Какие поля отображать в панели администратора
    list_display = ["preview_image", "title", "created_at", "short_content", "tags_function", "user"]
    # Поля для поиска
    search_fields = ["title", "content"]
    date_hierarchy = "created_at"  # Можно выбирать конкретную дату

    # Действия
    actions = ["title_up"]

    # Поля, которые не имеют большого кол-ва уникальных вариантов!
    list_filter = ["user__username", "user__email", "tags__name"]

    filter_horizontal = ["tags"]

    readonly_fields = ["preview_image"]

    fieldsets = (
        # 1
        (None, {"fields": ("title", "user", "preview_image", "image", "tags")}),
        ("Содержимое", {"fields": ("content",)})
    )

    def get_queryset(self, request):
        return (
            Note.objects.all()
            .select_related("user")  # Вытягивание связанных данных из таблицы User в один запрос
            .prefetch_related("tags")  # Вытягивание связанных данных из таблицы Tag в отдельные запросы
        )

    #  Действие
    @admin.action(description="Upper Title")
    def title_up(self, form, queryset: QuerySet[Note]):
        queryset.update(title=Upper(F("title")))

    @admin.display(description="Содержимое")
    def short_content(self, obj: Note) -> str:
        return obj.content[:50]+"..."

    # Добавляем колонку "Теги" в панель админа
    @admin.display(description="Теги")
    def tags_function(self, obj: Note) -> str:
        tags = list(obj.tags.all())
        text = ""
        for tag in tags:
            text += f"<span style=\"color: blue;\">{tag}</span><br>"
        return mark_safe(text)
        #  mark-safe - чтобы HTML-код отображался не строкой, а код

    @admin.display(description="IMG")
    def preview_image(self, obj: Note) -> str:
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" height="128" />')
                                        #  .url - отображает картинку
        return "X"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "first_name", "last_name", "count_note", "is_active"]
    search_fields = ["username"]
    actions = ["lock_user", "unlock_user"]
    list_editable = ["is_active"]

    @admin.display(description="Количество заметок")
    def count_note(self, obj: Note) -> str:
        return obj.note_set.count()

    @admin.action(description="Заблокировать пользователя")
    def lock_user(self, form, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Разблокировать пользователя")
    def unlock_user(self, form, queryset):
        queryset.update(is_active=True)

    fieldsets = (
        # 1  tuple(None, dict)
        (None, {"fields": ("username", "password")}),

        # 2  tuple(str, dict)
        ("Персональная информация", {"fields": ("first_name", "last_name", "email", "phone")}),

        # 3  tuple(str, dict)
        (
            "Права пользователя",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),

        # 4  tuple(str, dict)
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )
