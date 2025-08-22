import cv2
import numpy as np


def stackImages(scale, imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    if not rowsAvailable and rows == 0:
        return None
    if rowsAvailable and (rows == 0 or len(imgArray[0]) == 0):
        return None
    first_image = imgArray[0][0] if rowsAvailable else imgArray[0]
    width = first_image.shape[1]
    height = first_image.shape[0]

    if rowsAvailable:
        for x in range(0, rows):
            for y in range(0, cols):
                imgArray[x][y] = cv2.resize(imgArray[x][y], (width, height))
                if len(imgArray[x][y].shape) == 2:
                    imgArray[x][y] = cv2.cvtColor(
                        imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        pass
    return ver


def resize_to_height(image, target_height):
    h, w = image.shape[:2]
    if h == 0:
        return image
    ratio = target_height / h
    target_width = int(w * ratio)
    return cv2.resize(image, (target_width, target_height))


def run_static_showcase(duration_ms=5000):
    TARGET_HEIGHT = 200

    path_p1 = r"C:\Users\myh\Desktop\Resources\p1.jpg"
    path_cards = r"C:\Users\myh\Desktop\Resources\cards.jpg"
    path_face = r"C:\Users\myh\Desktop\Resources\Thumbnail.jpg"
    path_cascade = r"C:\Users\myh\Desktop\Resources\haarcascade_frontalface_default.xml"

    img_p1 = cv2.imread(path_p1)
    img_face = cv2.imread(path_face)
    imgCards_for_display = cv2.imread(path_cards)
    if any(img is None for img in [img_p1, img_face, imgCards_for_display]):
        print("错误：一个或多个静态图片文件未找到。")
        return

    img_p1 = resize_to_height(img_p1, TARGET_HEIGHT)
    img_face = resize_to_height(img_face, TARGET_HEIGHT)
    imgCards_for_display = resize_to_height(
        imgCards_for_display, TARGET_HEIGHT)

    gray_p1 = cv2.cvtColor(img_p1, cv2.COLOR_BGR2GRAY)
    imgBlur_p1 = cv2.GaussianBlur(gray_p1, (7, 7), 0)
    imgCanny_p1 = cv2.Canny(img_p1, 100, 200)
    kernel = np.ones((3, 3), np.uint8)
    dilation_p1 = cv2.dilate(imgCanny_p1, kernel, iterations=1)
    erosion_p1 = cv2.erode(dilation_p1, kernel, iterations=1)
    imgCropped_p1 = img_p1[0:int(TARGET_HEIGHT/2), 0:int(img_p1.shape[1]/2)]

    faceCascade = cv2.CascadeClassifier(path_cascade)
    gray_face_resized = cv2.cvtColor(img_face, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(gray_face_resized, 1.1, 4)
    imgFaceDetect = img_face.copy()
    for (x, y, w, h) in faces:
        cv2.rectangle(imgFaceDetect, (x, y), (x + w, y + h), (0, 255, 0), 2)

    full_size_cards = cv2.imread(path_cards)
    width_orig, height_orig = 250, 350
    pts1 = np.float32([[111, 219], [287, 188], [154, 482], [352, 440]])
    pts2 = np.float32(
        [[0, 0], [width_orig, 0], [0, height_orig], [width_orig, height_orig]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgPerspective_extracted = cv2.warpPerspective(
        full_size_cards, matrix, (width_orig, height_orig))
    imgPerspective = resize_to_height(imgPerspective_extracted, TARGET_HEIGHT)

    img_blank = np.zeros_like(img_p1)
    cv2.putText(img_blank, "Drawing", (30, 100),
                cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)

    imgArray = [
        [img_p1, gray_p1, imgBlur_p1, imgCanny_p1],
        [dilation_p1, erosion_p1, imgCropped_p1, img_blank],
        [img_face, imgFaceDetect, imgCards_for_display, imgPerspective]
    ]
    stacked_images = stackImages(1.0, imgArray)

    cv2.imshow("OpenCV Showcase (3x4 Layout)", stacked_images)
    cv2.waitKey(duration_ms)
    cv2.destroyAllWindows()


def run_realtime_object_tracking():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误：无法打开摄像头。")
        return

    def empty(a): pass
    cv2.namedWindow("TrackBars")
    cv2.resizeWindow("TrackBars", 640, 240)
    cv2.createTrackbar("Hue Min", "TrackBars", 0, 179, empty)
    cv2.createTrackbar("Hue Max", "TrackBars", 19, 179, empty)
    cv2.createTrackbar("Sat Min", "TrackBars", 110, 255, empty)
    cv2.createTrackbar("Sat Max", "TrackBars", 240, 255, empty)
    cv2.createTrackbar("Val Min", "TrackBars", 153, 255, empty)
    cv2.createTrackbar("Val Max", "TrackBars", 255, 255, empty)

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        imgHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        h_min = cv2.getTrackbarPos("Hue Min", "TrackBars")
        h_max = cv2.getTrackbarPos("Hue Max", "TrackBars")
        s_min = cv2.getTrackbarPos("Sat Min", "TrackBars")
        s_max = cv2.getTrackbarPos("Sat Max", "TrackBars")
        v_min = cv2.getTrackbarPos("Val Min", "TrackBars")
        v_max = cv2.getTrackbarPos("Val Max", "TrackBars")

        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])
        mask = cv2.inRange(imgHSV, lower, upper)

        imgResult = cv2.bitwise_and(frame, frame, mask=mask)

        img_tracking_stacked = stackImages(
            0.8, ([frame, imgHSV], [mask, imgResult]))

        if img_tracking_stacked is not None:
            cv2.imshow("Real-time Object Tracking (4 Views)",
                       img_tracking_stacked)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_static_showcase(duration_ms=5000)
    run_realtime_object_tracking()
