import re
import cv2
import numpy as np
import toolsutil
import matplotlib.pyplot as plt

def filter_char(name):
    """
       检测文字是否存在在饮片操作方式列表
    """
    if name in toolsutil.opt_arr:
        return False
    return True


def find_numbers(input_str):
    """
        检测文字中的数字
    """
    result_arr = re.findall(r'\d+', input_str)
    if len(result_arr):
        return result_arr[len(result_arr) - 1]
    else:
        return None


def crop_img(dis_img, py_x):
    """
       裁剪图片中的饮片和处方号信息图片
    """
    dis_img_h, dis_img_w = dis_img.shape[:2]
    # 截取处方饮片内容
    x, y, w, h = 270 + py_x, 170, dis_img_w - 270, 330
    cropped_image = dis_img[y:y + h, x:x + w]
    # 截取处方剂数和处方号内容
    x_yz, y_yz, w_yz, h_yz = 270 + py_x, 500, dis_img_w - 270, dis_img_h-500
    cropped_image_yz = dis_img[y_yz:y_yz + h_yz, x_yz:x_yz + w_yz]
    return cropped_image, cropped_image_yz


def merge_ocr_p(ocr_arr):
    """
        合并同一位置的饮片信息，饮片名、剂量、煎药方式
    """
    ocr_arr = sorted(ocr_arr, key=lambda x: x[0][0][1])   # 由于处方打印存在倾斜情况，识别的文字不一定是按实际顺序，需要重新排序
    i = 0
    if len(ocr_arr) > 0:
        # 合并饮片同一位置的数据（饮片名和饮片重量）
        while i < len(ocr_arr):
            j = i + 1
            box1 = ocr_arr[i]
            if not filter_char(box1[1][0]):
                while j < len(ocr_arr):
                    box2 = ocr_arr[j]
                    if box2[0][0][1] - box1[0][0][1] <= 22:
                        box1 = [
                            [[box1[0][0][0], box1[0][0][1]], [0, 0], [box2[0][2][0], max(box1[0][2][1], box2[0][2][1])],
                             [0, 0]], ["{}{}".format(box1[1][0], box2[1][0]), 0.9]]
                        ocr_arr.remove(box2)
                        continue
                    j += 1
                ocr_arr[i] = box1
            i += 1
    return ocr_arr


def analysis_recipel(dis_img, file_path, py_x):
    """
       解析处方信息
    """
    img, cropped_image_yz = crop_img(dis_img, py_x)  # 裁剪
    file = file_path + '/recipel_img_herbal.jpg'
    img_h, img_w = img.shape[:2]
    yz_h, yz_w = cropped_image_yz.shape[:2]
    white_bg = np.ones((img_h + yz_h, max(img_w, yz_w), 3), dtype=np.uint8) * 255  # 生成空白背景图片
    white_bg[0:img_h, 0:yz_w] = img   # 放置处方图片
    white_bg[img_h:img_h + yz_h, 0:yz_w] = cropped_image_yz  # 放置处方剂数和处方号图片
    cv2.imencode('.jpg', white_bg)[1].tofile(file)

    ocr_url = '{}?file={}'.format(toolsutil.ocr_server_url, file)
    content_result = toolsutil.get_request(ocr_url)   # 请求文字识别服务
    print("content_result",content_result)
    if content_result.get('status') == '200':
        return get_herbal_sort(content_result, img_h, white_bg)
    return None, None


def get_herbal_sort(content_result, img_h, white_bg):
    """
      根据饮片位置，对饮片进行排序
    """
    position = content_result.get('position')
    result = []
    reciple_arr = []
    if position != [None]:
        ocr_arr1, ocr_arr2, ocr_arr3, ocr_arr4 = [], [], [], []
        for idx in range(len(position)):  # 遍历position
            res = position[idx]
            for line in res:
                if line[0][2][1] >= img_h:  # 剂数文字数据
                    if float(line[1][1]) < 0.8:
                        continue
                    reciple_arr.append(line[1][0])
                else:  # 饮片文字数据
                    max_x = max(line[0][0][0], line[0][1][0], line[0][2][0], line[0][3][0])
                    min_x = min(line[0][0][0], line[0][1][0], line[0][2][0], line[0][3][0])

                    if not filter_char(line[1][0]):  # 判断文本是否是饮片操作方式
                        pass
                    elif max_x - min_x < 45:  # 过滤掉手写文字
                        continue
                    max_y = max(line[0][0][1], line[0][1][1], line[0][2][1], line[0][3][1])
                    min_y = min(line[0][0][1], line[0][1][1], line[0][2][1], line[0][3][1])

                    if max_y - min_y > 45:  # 过滤掉印章文字，多行文本一起的文字
                        continue

                    if max_x > 100:  # 过滤掉盖章在左侧的文字
                        # print(line[1][0], max_x)  # 饮片最大x坐标
                        # print(line[1][0], max_y-min_y)  # 饮片信息文字高度，最大y坐标减去最小y坐标
                        if float(line[1][1]) < 0.8:
                            continue
                        if max_x < 200:
                            ocr_arr1.append(line)
                        elif max_x < 400:
                            ocr_arr2.append(line)
                        elif max_x < 600:
                            ocr_arr3.append(line)
                        else:
                            ocr_arr4.append(line)

                    # 标注识别文字区域
                    # cv2.rectangle(white_bg, (int(min_x), int(min_y)), (int(max_x), int(max_y)), (255, 0, 255), 1)
        # 显示标注好的图片
        # cv2.namedWindow('white_bg', 0)
        # cv2.imshow('white_bg', white_bg)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        ocr_arr1 = merge_ocr_p(ocr_arr1)  # 存在饮片名和剂量分开的情况，需要进行合并同一位置的饮片信息
        ocr_arr2 = merge_ocr_p(ocr_arr2)  # 存在饮片名和剂量分开的情况，需要进行合并同一位置的饮片信息
        ocr_arr3 = merge_ocr_p(ocr_arr3)  # 存在饮片名和剂量分开的情况，需要进行合并同一位置的饮片信息
        ocr_arr4 = merge_ocr_p(ocr_arr4)  # 存在饮片名和剂量分开的情况，需要进行合并同一位置的饮片信息

        len1 = len(ocr_arr1)
        len2 = len(ocr_arr2)
        len3 = len(ocr_arr3)
        len4 = len(ocr_arr4)
        max_arr = []
        if len1 > 0:
            max_arr.append(max(ocr_arr1[0][0][2][1], ocr_arr1[0][0][3][1]))

        if len2 > 0:
            max_arr.append(max(ocr_arr2[0][0][2][1], ocr_arr2[0][0][3][1]))

        if len3 > 0:
            max_arr.append(max(ocr_arr3[0][0][2][1], ocr_arr3[0][0][3][1]))

        if len4 > 0:
            max_arr.append(max(ocr_arr4[0][0][2][1], ocr_arr4[0][0][3][1]))

        max_all_y = max(max_arr)
        min_all_y = min(max_arr)  # 第一行距离顶部的偏离值
        if max_all_y - min_all_y > 20:  # 考虑到打印的处方存在纸盒不齐，导致处方信息左倾斜或者右倾斜，导致行高不一致，导致行高计算错误，所以需要加上10
            min_all_y = min_all_y + 10

        len_r = max(len1, len2, len3, len4)
        for i in range(len_r):
            min_y = (i - 0) * 36 + min_all_y  # 定义i行的y坐标值（行高+距离顶部的偏离值）
            # 取i行第一列饮片数据
            ocr_json_obj1, ocr_arr1, y1 = get_ocr_arr_p(ocr_arr1, min_y)
            result.append(set_ocr_arr_val(ocr_json_obj1))

            # 取i行第二列饮片数据
            ocr_json_obj2, ocr_arr2, y2 = get_ocr_arr_p(ocr_arr2, min_y)
            result.append(set_ocr_arr_val(ocr_json_obj2))

            # 取i行第三列饮片数据
            ocr_json_obj3, ocr_arr3, y3 = get_ocr_arr_p(ocr_arr3, min_y)
            result.append(set_ocr_arr_val(ocr_json_obj3))

            # 取i行第四列饮片数据
            ocr_json_obj4, ocr_arr4, y4 = get_ocr_arr_p(ocr_arr4, min_y)
            result.append(set_ocr_arr_val(ocr_json_obj4))
    return 'spl'.join(map(str, result)), 'spl'.join(map(str, reciple_arr))


def set_ocr_arr_val(ocr_json_obj):
    """
        从对应的行列位置取饮片信息
    """
    if ocr_json_obj is None:
        return '空无0g'
    else:
        result_name = '{}spl'.format(ocr_json_obj)
        result_name = toolsutil.replace_end_str(result_name, 'spl')
        if toolsutil.find_numbers_in_string(result_name) is None:
            return "{}0g".format(result_name)
        else:
            return result_name


def get_ocr_arr_p(ocr_p_arr, max_y):
    for ocr_p in ocr_p_arr:
        max_p_y = max(ocr_p[0][2][1], ocr_p[0][3][1])
        if abs(max_y - max_p_y) <= 20:
            ocr_p_arr.remove(ocr_p)
            return ocr_p[1][0], ocr_p_arr, max_p_y
    return None, ocr_p_arr, 0


def read_chufang_content(recipel_img, file_path):
    """
       读取处方文字信息
    """
    try:
        dis_img = recipel_img.copy() 
        content, content_yz = analysis_recipel(dis_img, file_path, 0)  # 解析饮片信息
        if content is not None:  # 匹配到饮片信息
            content = toolsutil.replace_end_str(content, 'spl空无0g')
            content_yz = content_yz.replace(' ', '')
            recipel_arr = re.findall(r'{}(.*?){}'.format("时间", 'spl'), content_yz)  # 匹配处方时间
            recipel_no_time = str(''.join(recipel_arr))
            if len(recipel_no_time) > 11:
                recipel_no_time = recipel_no_time[:12]

            matches = re.findall(r'\d{4}', content_yz)  # 匹配处方号
            recipel_no = None
            if len(matches) > 0:
                recipel_no = matches[len(matches) - 1]

            content_recipel = "{}{}".format(recipel_no_time, recipel_no)  # 拼接处方号
            content_recipel = content_recipel.replace('-', '')
            return content, recipel_img, content_yz, '', {"diagnose": "", "bar_code": content_recipel, "receipel_no": recipel_no}
    except Exception as e:
        print(e)
    return '', None, None, None, None


if __name__ == '__main__':
    file_path = '{}/recipel_img.jpg'.format(toolsutil.localDir)
    recipel_img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
    if recipel_img is not None and 600 < recipel_img.shape[0] < 830:
        herbal_content, dis_img, yz_content, base_content, recipel_obj = read_chufang_content(recipel_img, toolsutil.localDir)
        herbal_json = toolsutil.get_herbal_json(herbal_content)
        print(herbal_json)

        taboo_results = toolsutil.get_taboos(herbal_json)
        print(taboo_results)

