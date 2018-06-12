from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def request_neo(request):

    if request.method == 'GET':
        data = request.GET

    elif request.method == 'POST':
        data = request.POST

    else:
        print("no data")
        return HttpResponse('401')


    my_request = dict(date.iterlists())

    print(data)
    return HttpResponse('200')
