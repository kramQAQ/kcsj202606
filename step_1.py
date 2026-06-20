import cv2
import numpy

img = cv2.imread("data/2a1aa19631a5718d2f11e55bd7eb2d12.jpg")
# 定义黄色范围
# lower_yellow = numpy.array([26, 43, 46])
lower_yellow = numpy.array([20, 43, 46])
upper_yellow = numpy.array([34, 255, 255])

# 转换到HSV空间
hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# 创建二值掩膜图像
mask_img = cv2.inRange(hsv_img, lower_yellow, upper_yellow)

# 显示二值掩膜图像
cv2.namedWindow("mask_img", cv2.WINDOW_NORMAL)
cv2.resizeWindow("mask_img", int(img.shape[1] / 3), int(img.shape[0] / 3))
cv2.imshow("mask_img", mask_img)
cv2.waitKey(0)
cv2.destroyAllWindows()
# 形态学处理二值掩膜图像
kernel = numpy.ones((15, 15), numpy.uint8)
# 填充前景区域中的小孔洞并连接邻近的区域，从而得到更完整、平滑的目标区域
mask = cv2.morphologyEx(mask_img, cv2.MORPH_CLOSE, kernel)

# 显示通过形态学膨胀后的二值掩膜图像
cv2.namedWindow("mask", cv2.WINDOW_NORMAL)
cv2.resizeWindow("mask", int(img.shape[1] / 3), int(img.shape[0] / 3))
cv2.imshow("mask", mask)
cv2.waitKey(0)
cv2.destroyAllWindows()
# 轮廓检测
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contour_arr = []
category_arr = []
for contour in contours:
    area = cv2.contourArea(contour)
    if area > 50000:  # 可以调整此阈值来过滤小移动
        contour_arr.append(contour)
        category_arr.append(0)

new_img = img.copy()
if len(contour_arr) > 0:
    cv2.drawContours(new_img, contour_arr, -1, (0, 255, 0), 3)

# 显示结果
cv2.namedWindow("new_img", cv2.WINDOW_NORMAL)
cv2.resizeWindow("new_img", int(new_img.shape[1] / 3), int(new_img.shape[0] / 3))
cv2.imshow("new_img", new_img)
cv2.waitKey(0)
cv2.destroyAllWindows()