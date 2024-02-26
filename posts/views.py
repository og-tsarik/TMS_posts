from django.shortcuts import render
from django.urls import reverse
from django.db.models import Q, F
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, HttpRequest
from django.core.handlers.wsgi import WSGIRequest

from .models import Note, User, Tag
from .service import create_note, filter_notes, queryset_optimization


def home_page_view(request: HttpRequest):
    # Обязательно! каждая функция view должна принимать первым параметром request.
    all_notes = Note.objects.all()  # Получение всех записей из таблицы этой модели.

    queryset = queryset_optimization(Note.objects.all())

    context: dict = {
        "notes": all_notes
    }

    # return render(request, "home.html", context)
    return render(request, "home.html", {"notes": queryset[:100]})


def filter_notes_view(request: WSGIRequest):
    """
    Фильтруем записи по запросу пользователя.
    HTTP метод - GET.
    Обрабатывает URL вида: /filter/?search=<text>
    """

    search: str = request.GET.get("search", "")  # `get` - получение по ключу. Если такого нет, то - "",
    queryset = queryset_optimization(
        filter_notes(search)
    )

    context: dict = {
        "notes": queryset[:100],
        "search_value_form": search,
    }
    return render(request, "home.html", context)


@login_required
def create_note_view(request: WSGIRequest):
    if request.method == "POST":
        note = create_note(request)
        return HttpResponseRedirect(reverse('show-note', args=[note.uuid]))

    # Вернется только, если метод не POST.
    return render(request, "create_form.html")


def show_note_view(request: WSGIRequest, note_uuid):
    try:
        note = Note.objects.get(uuid=note_uuid)  # Получение только ОДНОЙ записи.

    except Note.DoesNotExist:
        # Если не найдено такой записи.
        raise Http404

    return render(request, "note.html", {"note": note})


def delete_note_view(request: WSGIRequest, note_uuid):
    try:
        note = Note.objects.get(uuid=note_uuid)
        note.delete()
        return HttpResponseRedirect("/")
    except Note.DoesNotExist:
        raise Http404


def edit_note_view(request: WSGIRequest, note_uuid):
    try:
        note = Note.objects.get(uuid=note_uuid)

        if request.method == "POST":
            note = Note.objects.get(uuid=note_uuid)
            note.title = request.POST["title"]
            note.content = request.POST["content"]
            note.save()
            return HttpResponseRedirect("/")
        else:
            return render(request, "edit_form.html", {"note": note})
    except Note.DoesNotExist:
        raise Http404


def show_about_view(request: WSGIRequest):
    return render(request, "about.html")


def register(request: WSGIRequest):
    if request.method != "POST":
        return render(request, "registration/register.html")
    print(request.POST)
    if not request.POST.get("username") or not request.POST.get("email") or not request.POST.get("password1"):
        return render(
            request,
            "registration/register.html",
            {"errors": "Укажите все поля!"}
        )
    print(User.objects.filter(
            Q(username=request.POST["username"]) | Q(email=request.POST["email"])
    ))
    # Если уже есть такой пользователь с username или email.
    if User.objects.filter(
            Q(username=request.POST["username"]) | Q(email=request.POST["email"])
    ).count() > 0:
        return render(
            request,
            "registration/register.html",
            {"errors": "Если уже есть такой пользователь с username или email"}
        )

    # Сравниваем два пароля!
    if request.POST.get("password1") != request.POST.get("password2"):
        return render(
            request,
            "registration/register.html",
            {"errors": "Пароли не совпадают"}
        )

    # Создадим учетную запись пользователя.
    # Пароль надо хранить в БД в шифрованном виде.
    User.objects.create_user(
        username=request.POST["username"],
        email=request.POST["email"],
        password=request.POST["password1"]
    )
    return HttpResponseRedirect(reverse('home'))


def user_notes_view(request: WSGIRequest, username: str):
    queryset = queryset_optimization(
        Note.objects.filter(user__username=username)
    )
    # SELECT * FROM "posts_note"
    # INNER JOIN "users" ON ("posts_note"."user_id" = "users"."id")
    # WHERE "users"."username" = boris1992
    # ORDER BY "posts_note"."created_at" DESC

    print(Note.objects.filter(user__username=username).query)

    return render(request, "home.html", {"notes": queryset})


#def get_user_tags(user_id: int):
#    user_id_field = F("notes__user_id")
#    queryset = Tag.objects.select_related("notes").filter(Q(notes__user_id=user_id)).values('name')

#    return queryset


@login_required
def profile_view(request: WSGIRequest, username: str):
    if request.method == "POST":
        request.user.first_name = request.POST.get("firstname", None)
        request.user.last_name = request.POST.get("lastname", None)
        request.user.phone = request.POST.get("phone", None)
        request.user.save()

#    tags = get_user_tags(request.user.id)
    tags = Tag.objects.filter(notes__user__username=username).distinct()

    return render(request, "profile.html", {"tags": tags})
