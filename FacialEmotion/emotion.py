import cv2
from deepface import DeepFace
from fastapi import FastAPI
from pydantic import BaseModel
def read_image():
    face_casscade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml') # This is done to detect humans face with predefault markers such as ears,nose,eye
    cap = cv2.VideoCapture(0)
    face_image = None
    window  = "Please look at the window"
    if not cap.isOpened():
        return None
    while True:
        has_frame,frames = cap.read()
        if not has_frame:
            return None
        cv2.imshow(window,frames)
        gray = cv2.cvtColor(frames,cv2.COLOR_BGR2GRAY)
        faces = face_casscade.detectMultiScale(gray,scaleFactor=1.05,minNeighbors=3,minSize=(30,30)) # Detects the  facial features
        for (x,y,w,h) in faces:
            cv2.rectangle(frames,(x,y),(x+w,y+h),(0,255,0),2) # should create a rectangle around the captured face
        key = cv2.waitKey(1) # waiting to enter a key
        if(key == ord('q') or key == ord('Q')): # The main loop should exit when q or Q is pressed which is short for quit
            if len(faces) > 0: # if face is captured 
                (x,y,w,h) = faces[0]
                face_image = frames[y:y+h,x:x+w]
            break
    cap.release()
    cv2.destroyAllWindows()
    return face_image # face_image contains the cropped version of your face which also contains the rectangle 
def detectEmotion(face_image):
    analysis = DeepFace.analyze(face_image,actions=['emotion'],enforce_detection=False)
    return analysis[0]['dominant_emotion']
app = FastAPI()
class EmotionalRespone(BaseModel):
    status:str
    dominantEmotion:str
@app.post("/emotion",response_model = EmotionalRespone)
async def sendRequest():
    image = read_image()
    if image is None:
        return {
            "status" : "image not found",
            "dominantEmotion" : ""
        }
    emotion = detectEmotion(image)
    return {
        "status":"success",
        "dominantEmotion" : emotion
    }
