from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView
from django.contrib import messages
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
#from LetsNote.middleware.http import Http403
from django.http import HttpResponseForbidden
from .models import Notes, Note_Tag
from .forms import NoteForm

# User defined objects here.

shorten_text = lambda text: text[:27] + '...' if len(text) > 30 else text


class AbstractNote:
    def __init__(self, id, title, note_text, last_modified, tags_list):
        self.id = id
        self.title = title
        self.note_text = note_text
        self.last_modified = last_modified
        self.tags_list = tags_list


def concatTags(note_obj, as_string=False):
    note_obj_tags = note_obj.note_tag_set.all()
    tags_list = [tag.tag_text for tag in note_obj_tags]
    #tag_string = ','.join(tags_list)
    if as_string:
        return ','.join(tags_list)
    return tags_list


def send_email(user_email, subject, message, recipient_list):
    subject = subject
    email_from = user_email
    send_mail(subject, message, email_from, recipient_list)
    #return HttpResponse("I am done")


# Create your views here.


def home(request):
    return render(request, 'notes/home.html', {})


@login_required
def notes_home(request, tag=None):
    if tag:
        notes = Notes.objects.filter(user=request.user, note_tag__tag_text=tag.lower()).order_by('-last_modified')
    elif request.method == "POST":
        tag = request.POST["tag-search"]
        tags = tag.lower().replace(",", " ").split()
        #notes = Notes.objects.filter(user=request.user, note_tag__tag_text=tag).order_by('-last_modified')
        notes = Notes.objects.filter(user=request.user)
        for tag_indie in tags:
            notes = notes.filter(user=request.user, note_tag__tag_text=tag_indie.strip()).order_by('-last_modified')
        if tag.lower().strip() == '':
            notes = Notes.objects.filter(user=request.user).order_by('-last_modified')
    else:
        notes = Notes.objects.filter(user=request.user).order_by('-last_modified')

    notesList = [AbstractNote(N.id, N.title, shorten_text(N.note_text), N.last_modified, concatTags(N)) for N in notes]

    context = {
        'notes': notesList,
        'userNotesExists': bool(Notes.objects.filter(user=request.user)),
        'title': 'Home',
        'existing_tag': tag.strip().lower() if tag else ''
    }
    return render(request, 'notes/notes_home.html', context=context)


@login_required
def noteDetailView(request, pk):
    if Notes.objects.get(pk=pk).user != request.user:
        response = TemplateResponse(request, 'notes/403.html', {})
        response.render()
        return HttpResponseForbidden(response)

    note_obj = Notes.objects.get(pk=pk)
    tag_list = concatTags(note_obj)
    print(tag_list)
    context = {
        'note_id': note_obj.id,
        'title': note_obj.title,
        'last_modified': note_obj.last_modified,
        'note_text': note_obj.note_text,
        'tags': tag_list
    }
    return render(request, 'notes/notes_detail.html', context=context)


@login_required
def addNote(request):
    if request.method == "POST":
        tags =  request.POST["tags"]
        tags = tags.lower().replace(",", " ").split()

        note_obj = Notes(title=request.POST["title"], note_text=request.POST["note_text"], user=request.user)
        note_obj.save()

        for tag in tags:
            Note_Tag.objects.create(note=note_obj, tag_text=tag)

        messages.success(request, 'Added note successfully!')
        return redirect('notes-home')
    #messages.warning(request, 'Tags must NOT contain spaces or commas within them.')
    return render(request,'notes/addnote.html', {'title': 'Add Note'})


@login_required
def edit_note(request, pk):
    pk_list = [note.id for note in request.user.notes_set.all()]
    if pk not in pk_list:
        response = TemplateResponse(request, 'notes/403.html', {})
        response.render()
        return HttpResponseForbidden(response)

    note = Notes.objects.get(pk=pk)

    if request.method == "POST":
        nf = NoteForm(request.POST, instance=note)
        tag_set = note.note_tag_set.all()
        tag_set.delete()

        tags =  request.POST["tags"]
        tags = tags.lower().replace(",", " ").split()

        for tag in tags:
            Note_Tag.objects.create(note=note, tag_text=tag)

        if nf.is_valid():
            nf.save()
            messages.success(request, 'Successfully updated note!')
            return redirect('notes-home')
    else:
        nf = NoteForm(instance=note)

    return render(request, 'notes/edit_note.html', {"form": nf, "note":note, "title": "Update Note", "note_id": note.id})


@login_required
def deleteNote(request, pk):
    pk_list = [note.id for note in request.user.notes_set.all()]
    if pk not in pk_list:
        response = TemplateResponse(request, 'notes/403.html', {})
        response.render()
        return HttpResponseForbidden(response)

    Notes.objects.filter(pk=pk).delete()
    messages.success(request, 'Note has been deleted successfully.')
    return redirect('notes-home')


@login_required
def shareNote(request, pk):
    pk_list = [note.id for note in request.user.notes_set.all()]
    if pk not in pk_list:
        response = TemplateResponse(request, 'notes/403.html', {})
        response.render()
        return HttpResponseForbidden(response)
    context = {
        'pk': pk,
        'title': 'Share Note'
    }
    return render(request, "notes/sharenote.html", context=context)


@login_required
def completeSharing(request):
    if request.method == "POST":
        pk = request.POST["pk"]
        note_to_send = Notes.objects.filter(pk=pk)[0]

        recipients_list = []
        for key in request.POST:
            if key.startswith("email-recipient-"):
                recipients_list.append(request.POST[key])

        if not recipients_list:
            messages.info(request, 'Add at least one recipient email before sharing.')
            return redirect('/sharenote/{}'.format(pk))

        print(request.user.email, note_to_send.title, note_to_send.note_text, recipients_list, sep="\n")

        text_to_send = f"{request.user.username} is sharing the following text with you.\n\n" + note_to_send.note_text

        send_email(
            user_email = request.user.email,
            subject = note_to_send.title,
            message = text_to_send,
            recipient_list = recipients_list
        )

        messages.success(request, 'Emails sent successfully.')
        return redirect('/home/notes/' + str(pk))
    return redirect('/home/')
