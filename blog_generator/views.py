from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,logout,login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.conf import settings
from pytubefix import YouTube
import os
import assemblyai as aai
import openai

# Create your views here.
@login_required
def index(request):
    return render(request,'index.html')

@csrf_exempt
def generate_blog(request):
    print("Generating...")
    if(request.method=='POST'):
        
        testData = json.loads(request.body)
        print(testData)
        try:
            print("trying..")
            data=json.loads(request.body)
            print(data)
            yt_link=data['link']
            print(yt_link)
        except (KeyError,json.JSONDecodeError):
            return JsonResponse({'error':'invalid request method'},status=400)
           
        # get yt title
        title=yt_title(yt_link)
        print("About to transipt")
        # get transcript
        transcription=get_transcription(yt_link)
        print("Transpited..")
        print(transcription)
        if not transcription:
            return JsonResponse({'error':"failed to get transcript"},status=500)
        
        # use open ai to generate the blog
        blog_content=generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error':"failed to get transcript"},status=500)
        # save blog article to the database

        # return blog article as a response
        return JsonResponse({'content':blog_content})
    else:
        return JsonResponse({'error':'invalid request method'},status=405)
    
def yt_title(link):
    yt=YouTube(link)
    title=yt.title
    return title

def download_audio(link):
    print(link)
    yt=YouTube(link)
    print(yt)
    video=yt.streams.filter(only_audio=True).first()
    print(yt.streams.filter(progressive=True).all())
    print("Video", video)

    out_file=video.download(output_path=settings.MEDIA_ROOT)
    print("Out", out_file)
    base,ext=os.path.splitext(out_file)
    print("Base", base)
    new_file=base+'.mp3'
    os.rename(out_file,new_file)
    print(new_file)
    return new_file

def get_transcription(link):
    print('Trans')
    audio_file=download_audio(link)
    print("Audio",audio_file)
    aai.settings.api_key="487dde5c25bc40bfa090f83ca3d09765"

    print("Transibing..")
    transcriber=aai.Transcriber()
    print("Trans loaded")
    transcript=transcriber.transcribe(audio_file)
    print("Trans complete: ")
    print(transcript)

    return transcript.text

def generate_blog_from_transcription(transcription):
    openai.api_key="sk-7a6nlpLftFaxI-J9hV_B36Mq-FP48H3SbwZNtREzpwT3BlbkFJuNRcYHoe3Kfwjts9u0QPnnqRgjKEM5KI1Rfk3kHdQA"
    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"
    response=openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=1000
    )
    generated_content=response.choices[0].text.strip()
    return generated_content

def user_login(request):
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect("/")
        else:
            error_message="invalid username or password"
            return render(request,'login.html',{'error_message':error_message})
    
    return render(request,'login.html')

def user_signup(request):
    if request.method=='POST':
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        repeatpassword=request.POST['repeatpassword']

        if password==repeatpassword:
            try:
                user=User.objects.create_user(username,email,password)
                user.save()
                login(request,user)
                return redirect('/')
            except Exception as e:
                if User.objects.filter(username=username).exists()==True:
                    error_message="user already exist"
                elif User.objects.filter(email=email).exists()==True:
                    error_message="email already exist"
                else:
                    error_message="Error creating account"
                return render(request,'signup.html',{"error_message":error_message})
        else:
            error_message="password do not match"
            return render(request,'signup.html',{"error_message":error_message})
    return render(request,'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')