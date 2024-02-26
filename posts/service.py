from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet, Q, F
from django.contrib.postgres.aggregates import ArrayAgg

from posts.models import Note, Tag


def create_note(request: WSGIRequest) -> Note:
    note = Note.objects.create(
        title=request.POST["title"],
        content=request.POST["content"],
        user=request.user,
        image=request.FILES.get("noteImage"),
    )

    # Если нет тегов, то будет пустой список
    tags_names: list[str] = request.POST.get("tags", "").split(",")
    tags_names = list(map(str.strip, tags_names))  # Убираем лишние пробелы через 'strip'

    tags_objects: list[Tag] = []
    for tag in tags_names:
        tag_obj, created = Tag.objects.get_or_create(name=tag)
        tags_objects.append(tag_obj)

    note.tags.set(tags_objects)  # `set` это переопределение всех тегов для заметки.

    return note


def filter_notes(search: str) -> QuerySet[Note]:
    # Если строка поиска не пустая, то фильтруем записи по ней.
    if search:
        # ❗️Нет обращения к базе❗️
        # Через запятую запросы формируются c ❗️AND❗️
        # notes_queryset = Note.objects.filter(title__icontains=search, content__icontains=search)
        # SELECT "posts_note"."uuid", "posts_note"."title", "posts_note"."content", "posts_note"."created_at"
        # FROM "posts_note" WHERE (
        # "posts_note"."title" LIKE %search% ESCAPE '\' AND "posts_note"."content" LIKE %search% ESCAPE '\')

        # ❗️Все импорты сверху файла❗️
        # from django.db.models import Q

        notes_queryset = Note.objects.filter(title__icontains=search, content__icontains=search)
        # Аналогия
        notes_queryset = Note.objects.filter(Q(title__icontains=search), Q(content__icontains=search))

        # Оператор - `|` Означает `ИЛИ`.
        # Оператор - `&` Означает `И`.
        # notes_queryset = Note.objects.filter(Q(title__icontains=search) | Q(content__icontains=search))
        notes_queryset = Note.objects.filter(Q(title__icontains=search) | Q(content__icontains=search))

    else:
        # Если нет строки поиска.
        notes_queryset = Note.objects.all()  # Получение всех записей из модели.

    notes_queryset = notes_queryset.order_by("-created_at")  # ❗️Нет обращения к базе❗️

    # SELECT "posts_note"."uuid", "posts_note"."title", "posts_note"."content", "posts_note"."created_at"
    # FROM "posts_note" WHERE
    # ("posts_note"."title" LIKE %python% ESCAPE '\' OR "posts_note"."content" LIKE %python% ESCAPE '\')
    # ORDER BY "posts_note"."created_at" DESC

    print(notes_queryset.query)

    return notes_queryset


def queryset_optimization(queryset: QuerySet[Note]) -> QuerySet[Note]:
    return (
        queryset  # Запрос
        .select_related("user")  # Вытягивание связанных данных из таблицы User в один запрос
        .prefetch_related("tags")  # Вытягивание связанных данных из таблицы Tag в отдельные запросы
        .annotate(
            # Создание нового вычисляемого поля username из связанной таблицы User
            username=F('user__username'),

            # Создание массива уникальных имен тегов для каждой заметки
            tag_names=ArrayAgg('tags__name', distinct=True)
        )
        .values("uuid", "title", "created_at", "username", "tag_names")  # Выбор только указанных полей для результата
        .distinct()  # Убирание дубликатов, если они есть
        .order_by("-created_at")  # Сортировка результатов по убыванию по полю created_at
    )