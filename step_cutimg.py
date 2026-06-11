import cv2
import toolsutil
import numpy as np
import math


def check_contours(img, block_size=51, check_area=2500, constant=2):
    '''
        检测轮廓是否有处方
    '''
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # 高斯模糊
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # 自适应阈值
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block_size, constant)
    # 寻找轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_new = []
    if len(contours) > 0:
        for contour in contours:
            area = cv2.contourArea(contour)
            # 获取面积大于某个临界值的轮廓，保证取到的轮廓是实际物体
            if area > check_area:
                contours_new.append(contour)
    if len(contours_new) > 0:
        max_contours = None
        max_w = 0
        for contours in contours_new:
            x, y, w, h = cv2.boundingRect(contours)
            if max_w == 0:
                max_w = w
                max_contours = contours
            elif w > max_w:
                max_w = w
                max_contours = contours
        return True, '正常', max_contours
    else:
        return False, '未检测到处方信息', None


def cut_img(numpy_image, img_result_path, max_contour):
    area = cv2.contourArea(max_contour)
    if area > 20000:  # 轮廓面积大于20000为有效轮廓
        max_rect = cv2.minAreaRect(max_contour)  # 获取点集的旋转矩形，该矩形覆盖了与原始点集相同的区域，且面积最小
        max_box = cv2.boxPoints(max_rect)  # 返回四个顶点的坐标
        if len(max_box) == 4:
            approx = np.intp(max_box)
            ltx, lty, lbx, lby, rtx, rty, rbx, rby = toolsutil.find_corners_point(approx)  # 根据点坐标计算点位置
            print(ltx, lty, lbx, lby, rtx, rty, rbx, rby)
            # 仿射变换
            # 计算目标矩形的宽度和高度（基于勾股定理）
            # 宽度：取顶部边长和底部边长的最大值
            width = max(math.sqrt((rtx - ltx) ** 2 + (rty - lty) ** 2), math.sqrt((rbx - lbx) ** 2 + (rby - lby) ** 2))
            # 高度：取左侧边长和右侧边长的最大值
            height = max(math.sqrt((ltx - lbx) ** 2 + (lty - lby) ** 2), math.sqrt((rtx - rbx) ** 2 + (rty - rby) ** 2))

            # 将计算出的浮点数宽高转换为整数像素值
            width, height = int(width), int(height)
            # 准备透视变换所需的源点和目标点（必须为 float32 类型）
            # 源点：原图中检测到的四个角点位置
            pts1 = np.float32([[ltx, lty], [rtx, rty], [lbx, lby], [rbx, rby]])
            # 目标点：期望矫正后的标准矩形坐标（从左上角(0,0)开始）
            pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
            # 计算 3x3 的透视变换矩阵
            mp = cv2.getPerspectiveTransform(pts1, pts2)
            # 应用透视变换，生成矫正后的图像
            # borderMode=cv2.BORDER_CONSTANT 表示超出边界的部分用纯色填充
            # borderValue=(255, 255, 255) 指定填充颜色为白色
            dst = cv2.warpPerspective(numpy_image, mp, (width, height), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
            # 保存矫正后的图像
            cv2.imwrite(img_result_path, dst)
            return dst
    return None
if __name__ == '__main__':
    dst_folder = 'chufang2.jpg'
    numpy_image = cv2.imread(dst_folder)
    if numpy_image is not None:
        # 检测轮廓是否有处方
        flag, msg, max_contour = check_contours(numpy_image)
        if flag:
            cut_img(numpy_image, 'chufang_img2.jpg', max_contour)
        else:
            print(msg)