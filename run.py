#!/usr/bin/env python3

import json
import cv2
import sys
import time
import threading
import numpy as np
from datetime import datetime
from threading import Timer
from AISecurityCam import app
from AISecurityCam import tools
from AISecurityCam.DetectorAPI import DetectorAPI
from AISecurityCam.camera import VideoCamera
from flask import Response
from AISecurityCam.models import User, Records
from AISecurityCam import db
import imageio

UPDATE_INTERVAL = 5 # only once in this time interval
VIDEO_CAMERA = VideoCamera(flip=False) # creates a camera object, flip vertically
API = DetectorAPI()
THRESHOLD = 0.7

def check_for_objects():
    while True:
        # try:
        frame_in_bytes = VIDEO_CAMERA.get_frame()
        #Convert the frame from bytes to nparray so it can be processed by the API
        decoded = cv2.imdecode(np.frombuffer(frame_in_bytes, np.uint8), -1)
        boxes, scores, classes, num = API.processFrame(decoded)

        for i in range(len(boxes)):
            # Class 1 represents human
            if classes[i] == 1 and scores[i] > THRESHOLD:
                box = boxes[i]
                cv2.rectangle(decoded,(box[1],box[0]),(box[3],box[2]),(0,0,255),2)
                color_conversion = cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)
                now = datetime.now()
                imageio.imwrite('AISecurityCam/static/records/{}.jpg'.format(now.strftime("%d-%m-%Y_%H:%M:%S")), color_conversion)

                #update database
                new_record = Records(created_at = now.strftime("%Y-%m-%d"), file_type = "picture", path_filename = "{}.jpg".format(now.strftime("%d-%m-%Y_%H:%M:%S")))
                db.session.add(new_record)
                db.session.commit()

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(VIDEO_CAMERA),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def autoupdate():
	print("AUTO UPDATE THREAD STARTING")
	while True:
		print('autoupdate check')
		tools.update_config()
		time.sleep(60*60*2)


if __name__ == '__main__':
    cameras = [
        "rtsp://guest:8uW6g4f!@goranssonsakeri.mine.nu:8202",
        "rtsp://guest:8uW6g4f!@79.138.1.151:8203",
        "rtsp://guest:8uW6g4f!@79.138.1.151:8205",
        "rtsp://guest:8uW6g4f!@79.138.1.151:8208",
        "rtsp://guest:8uW6g4f!@talltank.dyndns.org:10004",
        "rtsp://guest:8uW6g4f!@yc2300.mine.nu:8002"
    ]

    t = threading.Thread(target=check_for_objects, args=())
    t.daemon = True
    t.start()

    autoupdateThread = threading.Thread(target=autoupdate)
    autoupdateThread.daemon = True
    autoupdateThread.start()

    #TODO CHECK EVERY ONCE AN HOUR IF THE IP ADDRESS IS THE SAME OR SEND MAIL WITH NEW ONE

    app.run(host='0.0.0.0', debug=False)

