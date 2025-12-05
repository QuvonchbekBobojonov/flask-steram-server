import cv2
import requests
import time

STREAM_NAME = "opencv_test"   # dinamik nom
PUSH_URL = f"http://127.0.0.1:8000/push/{STREAM_NAME}"

cap = cv2.VideoCapture(0)  # Web-kamerani ochish

if not cap.isOpened():
    print("Kamera ochilmadi!")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Kadr olinmadi!")
        break

    # JPEG formatga kodlash
    _, jpeg = cv2.imencode('.jpg', frame)

    # Flaskga push qilish
    try:
        requests.post(
            PUSH_URL,
            data=jpeg.tobytes(),
            headers={"Content-Type": "image/jpeg"},
            timeout=0.5
        )
    except Exception as e:
        print("Push error:", e)

    # Lokal ekranda ko‘rsatish (test uchun)
    cv2.imshow("Pushing to Flask", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
