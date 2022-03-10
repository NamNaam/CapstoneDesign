from django.views.decorators import gzip
from django.views.generic import View
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, HttpResponse, HttpResponseRedirect
#from django.utils import timezone
from django.urls import reverse
from .models import TempScore
#from django.template import loader

#모델 경로 관련
import os

#opencv&tensorflow
import cvlib as cv
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import ImageFont, ImageDraw, Image
#import threading

from rest_framework.response import Response
from rest_framework.views import APIView
from time import mktime, strptime

def index(request):
    if request.user.is_authenticated: #유저가 로그인 되어 있으면,
        return render(request, 'conc/mypage.html') #mypage.html을 렌더링
    return render(request, 'conc/index.html') #로그인 되어있지 않으면 index.html을 렌더링

def project(request):
    if request.method == "POST":
        return redirect('conc:result')
    return render(request, 'conc/project.html')

def result(request):
    return render(request, 'conc/result.html')

class VideoCamera(object):
    def __init__(self):
        self.model = load_model(os.path.dirname(__file__) + '/static/conc/model7.h5')
        self.video = cv2.VideoCapture(0)
        #(1)(self.status, self.frame) = self.video.read()
        #(1)threading.Thread(target=self.update, args=()).start()
        
    def __del__(self):
        self.video.release()

    def get_frame(self, user):
        (self.status, self.frame) = self.video.read()
        
        image = self.frame
        face, confidence = cv.detect_face(image)
        for idx, f in enumerate(face):
            (startX, startY) = f[0], f[1]
            (endX, endY) = f[2], f[3]
            if 0 <= startX <= image.shape[1] and 0 <= endX <= image.shape[1] and 0 <= startY <= image.shape[0] and 0 <= endY <= image.shape[0]:
                    face_region = image[startY:endY, startX:endX]
                    face_region1 = cv2.resize(face_region, (224, 224), interpolation=cv2.INTER_AREA)
                    x = img_to_array(face_region1)
                    x = np.expand_dims(x, axis=0)
                    x = preprocess_input(x)
                    prediction = self.model.predict(x)
                    
                    if prediction < 0.5:
                        score = TempScore(user=user, score=100)
                        score.save()
                        cv2.rectangle(image, (startX, startY), (endX, endY), (0,255,0), 2)
                        Y = startY - 10 if startY - 10 > 10 else startY + 10
                        text = "Concentrate ({:.2f}%)".format((1 - prediction[0][0])*100)
                        cv2.putText(image, text, (startX, Y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                    else:
                        score = TempScore(user=user, score=0)
                        score.save()
                        cv2.rectangle(image, (startX, startY), (endX, endY), (0,0,255), 2)
                        Y = startY - 10 if startY - 10 > 10 else startY + 10
                        text = "No concentrate ({:.2f}%)".format(prediction[0][0]*100)
                        cv2.putText(image, text, (startX, Y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        
        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
        #if cv2.waitkey(1) & 0xFF == ord('q'):
        #    break

    '''#1
    def update(self):
        while True:
            (self.status, self.frame) = self.video.read()
    '''

def gen(camera, user):
    while True:
        frame = camera.get_frame(user)
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@gzip.gzip_page        
def detect(request):
    try:
        cam = VideoCamera()
        return StreamingHttpResponse(gen(cam, request.user), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        print("error")
        pass
    
class ScoreAPIView(APIView):

    def get(self, request):
        stocks = TempScore.objects.filter(user=request.user).order_by('time')

        score_list = []
        dt = stocks[0].time
        score = 0
        count = 0
        for stock in stocks:
            if dt.minute == stock.time.minute and dt.hour == stock.time.hour and dt.date() == stock.time.date():
                score += stock.score
                count += 1
                continue

            avg_score = score // count
            time_tuple = strptime(str(dt), '%Y-%m-%d %H:%M:%S.%f')
            utc_now = mktime(time_tuple) * 1000
            score_list.append([utc_now, avg_score])

            dt = stock.time
            score = stock.score
            count = 1

        if count > 0:
            avg_score = score // count
            time_tuple = strptime(str(dt), '%Y-%m-%d %H:%M:%S.%f')
            utc_now = mktime(time_tuple) * 1000
            score_list.append([utc_now, avg_score])

        data = {
            'score': score_list,
        }

        return Response(data)