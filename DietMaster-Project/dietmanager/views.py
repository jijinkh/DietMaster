from sklearn.linear_model import LinearRegression
import joblib
from django.shortcuts import render
from django.http import *
from .forms import RegisterForm
from .models import HealthModel, StorageModel
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.template import RequestContext
import joblib
from sklearn.linear_model import LinearRegression
from .diets import getDiet
from annoying.functions import get_object_or_None

lr = joblib.load("caloriemeter.pkl")
# To register the user
def user_register(request):
    # if this is a POST request we need to process the form data
    template = 'dietmanager/register.html'

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            if User.objects.filter(username=form.cleaned_data['username']).exists():
                return render(request, template, {
                    'form': form,
                    'error_message': 'Username already exists.'
                })
            elif User.objects.filter(email=form.cleaned_data['email']).exists():
                return render(request, template, {
                    'form': form,
                    'error_message': 'Email already exists.'
                })
            elif form.cleaned_data['password'] != form.cleaned_data['password_repeat']:
                return render(request, template, {
                    'form': form,
                    'error_message': 'Passwords do not match.'
                })
            else:
                # Create the user:
                user = User.objects.create_user(
                    form.cleaned_data['username'],
                    form.cleaned_data['email'],
                    form.cleaned_data['password']
                )
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.phone_number = form.cleaned_data['phone_number']
                user.save()

                # Login the user
                login(request, user)

                # redirect to accounts page:
                return HttpResponseRedirect('/login/')

   # No post data availabe, let's just show the page.
    else:
        form = RegisterForm()

    return render(request, template, {'form': form})


# Check whether the user is registered and logs him in
def login_user(request, message=""):
	logout(request)
	username = ''
	password = ''
	if request.POST:
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect('/health/')
			else:
				print("Not active user")
		else:request, "dietmanager/health.html"
	return render(request, 'dietmanager/login.html', {message:"No such user found"})


# To get the health related details and store it in a db
@login_required(login_url='/login/')
def health(request):
    current_user = request.user

    if request.POST:
        forms = HealthModel()
        current_user = request.user
        forms.username = current_user
        forms.age = request.POST["age"]
        forms.weight = request.POST['weight']
        forms.height = request.POST['height']
        active = request.POST['is_active']
        forms.diseases = request.POST['diseases']
        if(active=="Very_Active"):
            forms.isActive = True
            forms.isnotActive = False
            forms.isModeratelyActive = False
        elif(active=="Moderately_Active"):
            forms.isActive = False
            forms.isnotActive = False
            forms.isModeratelyActive = True
        else:
            forms.isActive = False
            forms.isnotActive = True
            forms.isModeratelyActive = False
        gender = request.POST["gender"]
        if(gender=="Male"):
            forms.isMale = True
            forms.isFemale = False
        else:
            forms.isMale = False
            forms.isFemale = True
        try:
            v=HealthModel.objects.get(username=current_user)
        except:
            forms.save()
            v=HealthModel.objects.get(username=current_user)
        username=v.username
        age=int(v.age)
        ismale=int(v.isMale==True)
        isfemale=int(v.isFemale==True)
        weight=int(v.weight)
        height=int(v.height)
        isactive=int(v.isActive==True)
        isnotactive=int(v.isnotActive==True)
        ismoderate=int(v.isModeratelyActive==True)
        lib=[age,ismale,isfemale,height, weight, isactive, isnotactive, ismoderate,0,0,0]
        calories = lr.predict([lib])
        l2 = joblib.load("calories_to_nutrients.pkl")
        values = l2.predict(calories)
        v.calories = calories[0][0]
        v.carbs = values[0][0]
        v.proteins = values[0][1]
        v.fats = values[0][2]
        v.save()
        return render(request, "dietmanager/home.html",{"v":v})
    else:
        try:
            v = HealthModel.objects.get(username=current_user)
            return render(request, "dietmanager/home.html",{"v":v})
        except:
            return render(request, "dietmanager/health1.html")


# On Progress
@login_required(login_url='/login/')
def main(request):
    current_user = request.user
    obj = HealthModel.objects.all()
    return render(request, "dietmanager/home.html", {"user":current_user})


# Takes the food details
# Calculates the amount of nutrient intake and store it in a db
def getFood(request):
    from pandas import DataFrame, read_csv
    df = DataFrame(read_csv("foodData.csv"))

    user = request.user
    h = get_object_or_None(HealthModel, username=user)
    if not h:
        return render(request, 'dietmanager/getdiet.html', {"k":k})
    st = get_object_or_None(StorageModel, username=h)
    if not st:
        new_st = StorageModel()
        new_st.username = h
        new_st.save()
    k = df['name']
    k = set((list(k)))
    if request.POST:
        food_item = request.POST['fooditem']
        calories = df.loc[df['name'].isin([food_item])]
        quantity = request.POST['quantity']
        cals = calories.iloc[0]['calories'] * int(quantity)

        st.calories_to_take = (h.calories + st.calories_to_take) - cals

        st.save()

        return render(request, "dietmanager/home.html",{"v":h})

    else:
        return render(request, 'dietmanager/getdiet.html', {"k":k})
