import cv2
import numpy as np

# ==============================================================================
# 步骤 1: 图像拼接函数 (无需修改)
# ==============================================================================


def stackImages(scale, imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range(0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape[:2]:
                    imgArray[x][y] = cv2.resize(
                        imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(
                        imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]), None, scale, scale)
                if len(imgArray[x][y].shape) == 2:
                    imgArray[x][y] = cv2.cvtColor(
                        imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(
                    imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(
                    imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None, scale, scale)
            if len(imgArray[x].shape) == 2:
                imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor = np.hstack(imgArray)
        ver = hor
    return ver


# ==============================================================================
# 步骤 2: 定义所有文件路径 (请确认所有路径都正确)
# ==============================================================================
path_p1 = r"C:\Users\myh\Desktop\Resources\p1.jpg"  # 汽车图片
path_cards = r"C:\Users\myh\Desktop\Resources\cards.jpg"  # 扑克牌图片

# --- !!! 新增 !!! ---
# 请在这里提供一张有人脸的图片路径，例如 lena.png 或您自己的照片
path_face = r"C:\Users\myh\Desktop\Resources\Thumbnail.jpg"

# --- Haarcascade 文件路径 ---
path_cascade = r"C:\Users\myh\Desktop\Resources\haarcascade_frontalface_default.xml"


# ==============================================================================
# 步骤 3: 对汽车图片 (p1.jpg) 进行处理
# ==============================================================================
img_p1 = cv2.imread(path_p1)
if img_p1 is None:
    print(f"错误: 无法加载汽车图片 {path_p1}。")
    exit()

gray_p1 = cv2.cvtColor(img_p1, cv2.COLOR_BGR2GRAY)
imgBlur_p1 = cv2.GaussianBlur(gray_p1, (7, 7), 0)
imgCanny_p1 = cv2.Canny(img_p1, 150, 200)
kernel = np.ones((5, 5), np.uint8)
dilation_p1 = cv2.dilate(imgCanny_p1, kernel, iterations=1)
erosion_p1 = cv2.erode(dilation_p1, kernel, iterations=1)
imgCropped_p1 = img_p1[0:200, 200:500]


# ==============================================================================
# 步骤 4: **使用专门的人脸图片**进行人脸检测
# ==============================================================================
img_face = cv2.imread(path_face)
if img_face is None:
    print(f"错误: 无法加载人脸图片 {path_face}。请检查路径，并确保图片中有人脸。")
    exit()

faceCascade = cv2.CascadeClassifier(path_cascade)
if faceCascade.empty():
    print(f"错误: 无法加载 Haar Cascade 分类器 {path_cascade}")
    exit()

# 在人脸图片的灰度版本上进行检测
gray_face = cv2.cvtColor(img_face, cv2.COLOR_BGR2GRAY)
faces = faceCascade.detectMultiScale(gray_face, 1.1, 4)

# 在原始彩色人脸图片的副本上绘制矩形
imgFaceDetect = img_face.copy()
for (x, y, w, h) in faces:
    cv2.rectangle(imgFaceDetect, (x, y), (x + w, y + h), (255, 0, 0), 2)


# ==============================================================================
# 步骤 5: 透视变换 和 图像绘制 (保持不变)
# ==============================================================================
imgCards = cv2.imread(path_cards)
width, height = 250, 350
pts1 = np.float32([[111, 219], [287, 188], [154, 482], [352, 440]])
pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
matrix = cv2.getPerspectiveTransform(pts1, pts2)
imgPerspective = cv2.warpPerspective(imgCards, matrix, (width, height))

img_blank = np.zeros((512, 512, 3), np.uint8)
cv2.putText(img_blank, "Drawing Canvas", (30, 250),
            cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)


# ==============================================================================
# 步骤 6: 按照您要求的 3x4 布局进行拼接和显示
# ==============================================================================
imgArray = [
    [img_p1, gray_p1, imgBlur_p1, imgCanny_p1],
    [dilation_p1, erosion_p1, imgCropped_p1, img_blank],
    [img_face, imgFaceDetect, imgCards, imgPerspective]
]

# 调整缩放比例，以更好地适应3x4布局和您的屏幕
stacked_images = stackImages(0.3, imgArray)

cv2.imshow("OpenCV Showcase (3x4 Layout)", stacked_images)
cv2.waitKey(0)
cv2.destroyAllWindows()
