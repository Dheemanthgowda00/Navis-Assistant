import cv2
import pyttsx3
import threading
import time

# Initialize webcam
cap = cv2.VideoCapture(1)  # Use 0 for default webcam, 1 for external
cap.set(3, 640)
cap.set(4, 480)

# Cooldown mechanism to avoid repeating speech
last_spoken = {}
cooldown = 2  # seconds

# Load class names
classNames = []
classFile = r'C:\Users\user\PycharmProjects\NAVIS_ASSISTANT\Object_Detection\coco.names'  # Adjust path if needed
with open(classFile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

# Load model files
configPath = r'C:\Users\user\PycharmProjects\NAVIS_ASSISTANT\Object_Detection\ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'
weightsPath = r'C:\Users\user\PycharmProjects\NAVIS_ASSISTANT\Object_Detection\frozen_inference_graph.pb'

# Load the model
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1)

# Speak function in a separate thread
def speak(text):
    t = threading.Thread(target=lambda: _speak_internal(text))
    t.start()

def _speak_internal(text):
    engine.say(text)
    engine.runAndWait()

# Main detection loop
try:
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to capture image.")
            break

        classIds, confs, bbox = net.detect(img, confThreshold=0.55)
        if len(classIds) != 0:
            for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
                className = classNames[classId - 1].upper()
                cv2.rectangle(img, box, color=(0, 255, 0), thickness=3)
                cv2.putText(img, className, (box[0] + 10, box[1] + 30),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(img, str(round(confidence * 100, 2)) + '%',
                            (box[0] + 200, box[1] + 30),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

                # Speak only once every cooldown period
                now = time.time()
                if className not in last_spoken or now - last_spoken[className] > cooldown:
                    last_spoken[className] = now
                    speak(f"Detected {className}")

        # Show the output
        cv2.imshow("Output", img)

        key = cv2.waitKey(1)
        if key == ord('q'):
            speak("Exiting object detection.")
            break
except KeyboardInterrupt:
    print("Object detection interrupted.")
finally:
    cap.release()
    cv2.destroyAllWindows()
