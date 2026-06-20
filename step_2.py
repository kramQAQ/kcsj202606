import cv2
import numpy
img = cv2.imread("data/e91ed5641ef288811f5f7066bddd221f.jpg")
# 定义红色的HSV范围
lower_red1 = numpy.array([0, 43, 46])
upper_red1 = numpy.array([10, 255, 255])
lower_red2 = numpy.array([156, 43, 46])
upper_red2 = numpy.array([180, 255, 255])
# 转换到HSV空间
hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# 创建红色掩码
mask1 = cv2.inRange(hsv_img, lower_red1, upper_red1)
mask2 = cv2.inRange(hsv_img, lower_red2, upper_red2)
mask_img2 = mask1 + mask2
# 形态学处理
kernel = numpy.ones((15, 15), numpy.uint8)
mask2 = cv2.morphologyEx(mask_img2, cv2.MORPH_CLOSE, kernel)
# 轮廓检测
contours2, _ = cv2.findContours(mask_img2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contour_arr = []
category_arr = []
for contour in contours2:
    area = cv2.contourArea(contour)
    if area > 50000:  # 可以调整此阈值来过滤小移动
        contour_arr.append(contour)
new_img = img.copy()
if len(contour_arr) > 0:
    cv2.drawContours(new_img, contour_arr, -1, (0, 255, 0), 3)
# 显示结果
cv2.namedWindow("new_img", cv2.WINDOW_NORMAL)
cv2.resizeWindow("new_img", int(new_img.shape[1] / 3), int(new_img.shape[0] / 3))
cv2.imshow("new_img", new_img)
cv2.waitKey(0)
cv2.destroyAllWindows()