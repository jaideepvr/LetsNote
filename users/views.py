from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.template.response import TemplateResponse
from django.http import HttpResponseForbidden

from .tokens import account_activation_token
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm

# Create your views here.
def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            mail_subject = 'Verify your e-mail.'
            message = render_to_string('users/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user)
            })
            to_email = form.cleaned_data.get('email')

            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            #return HttpResponse('Please confirm your email address to complete registration.')
            messages.info(request, 'Please confirm your email address to complete registration.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    messages.warning(request, 'Your username cannot be changed later. Choose it wisely.')
    return render(request, 'users/register.html', {'form': form, 'title': 'Register'})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        #login(request, user)
        # return redirect('home')
        #return HttpResponse('Thank you for your email confirmation. Now you can login to your account.')
        messages.success(request, 'Thank you for your email confirmation. Now you can login to your account.')
    else:
        #return HttpResponse('Activation link is invalid!')
        messages.error(request, 'Activation link is invalid!')
    return redirect('login')


@login_required
def logout_user(request):
    logout(request)
    messages.success(request, 'You have successfully been logged out.')
    return redirect('login')


@login_required
def profile(request, username):
    if request.user.username == username:
        if request.method == "POST":
            u_form = UserUpdateForm(request.POST, instance=request.user)
            p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, 'Your profile has successfully been updated.')
                return redirect('/profile/{}'.format(request.user.username))
        else:
            u_form = UserUpdateForm(instance=request.user)
            p_form = ProfileUpdateForm(instance=request.user.profile)

        context = {
            'u_form': u_form,
            'p_form': p_form,
            'title': 'Profile'
        }
        return render(request, 'users/profile.html', context=context)
    response = TemplateResponse(request, 'notes/403.html', {})
    response.render()
    return HttpResponseForbidden(response)


@login_required
def deleteProfile(request):
    username = request.user.username
    logout(request)
    User.objects.filter(username=username).delete()
    messages.success(request, 'Account deleted!')
    return redirect('login')
