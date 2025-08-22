import numpy as np
import cv2
# cv2.imread(文件名，标记)读入图像
# LOAD AN IMAGE USING 'IMREAD'
img = cv2.imread(
    "D:/Egde/Robot small town/xiaoche/Resources/Resources/p1.jpg")
# DISPLAY
if img is not None:
    cv2.imshow("Lena Soderberg", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("无法加载图像")

# 转换为灰度图
gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
cv2.imshow('Gray Image', gray_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 将图像宽度调整为500像素，高度按比例缩放
ratio = 500.0 / img.shape[1]
dim = (500, int(img.shape[0] * ratio))
resized_image = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
cv2.imshow('Resized Image', resized_image)
cv2.waitKey(0)
cv2.destroyAllWindows()


# 调整亮度和对比度
# new_image = alpha * original_image + beta
alpha = 1.5  # 对比度控制
beta = 20    # 亮度控制
adjusted_image = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
cv2.imshow('Adjusted Image', adjusted_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 应用高斯模糊
# 核大小必须是奇数
blurred_image = cv2.GaussianBlur(img, (15, 15), 0)
cv2.imshow('Blurred Image', blurred_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Canny边缘检测
edges = cv2.Canny(img, 100, 200)
cv2.imshow('Edges', edges)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 首先将图像二值化
ret, binary_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)

# 定义一个核
kernel = np.ones((5, 5), np.uint8)

# 腐蚀操作
erosion = cv2.erode(binary_image, kernel, iterations=1)
cv2.imshow('Erosion', erosion)
cv2.waitKey(0)

# 膨胀操作
dilation = cv2.dilate(binary_image, kernel, iterations=1)
cv2.imshow('Dilation', dilation)
cv2.waitKey(0)
cv2.destroyAllWindows()
