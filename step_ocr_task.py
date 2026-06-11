import re
from pathlib import Path
import cv2
import numpy as np
import toolsutil
from paddle_ocr import ocr_image


def filter_char(name):
    """
       检测文字是否存在在饮片操作方式列表
    """
    if name in toolsutil.opt_arr:
        return False
    return True


def count_herbal_width(max_x, bit_len):
    """
        列的饮片数据没有获取到，根据前1列的饮片位置，推出当前饮片的位置坐标
    """
    if bit_len == 2:
        return max_x + 191, bit_len
    else:
        return max_x + 191, bit_len


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
    # 截取处方医嘱内容
    x_yz, y_yz, w_yz, h_yz = 270 + py_x, 500, dis_img_w - 270, 170
    cropped_image_yz = dis_img[y_yz:y_yz + h_yz, x_yz:x_yz + w_yz]
    return cropped_image, cropped_image_yz


def merge_ocr_p(ocr_arr):
    """
        合并同一位置的饮片信息，饮片名、重量、煎药方式
    """
    ocr_arr = sorted(ocr_arr, key=lambda x: x[0][0][1])
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


def rectMerge(ocr_arr):
    """
       根据列的文字及位置信息，获取饮片的坐标位置，最小坐标，饮片宽度
    """
    max_x1, max_y1, min_y1, bit_len = 0, 0, 0, 0
    i = 0
    ocr_arr = sorted(ocr_arr, key=lambda x: x[0][0][1])
    if len(ocr_arr) > 0:
        # 合并饮片同一位置的数据（饮片名和饮片重量）
        while i < len(ocr_arr):
            j = i + 1
            box1 = ocr_arr[i]
            while j < len(ocr_arr):
                box2 = ocr_arr[j]
                if box2[0][0][1] - box1[0][0][1] < 23:
                    result_num = find_numbers(box1[1][0])
                    if result_num is None:
                        box1 = [
                            [[box1[0][0][0], box1[0][0][1]], [0, 0], [box2[0][2][0], max(box1[0][2][1], box2[0][2][1])],
                             [0, 0]], ["{}{}".format(box1[1][0], box2[1][0]), 0.9]]
                        ocr_arr.remove(box2)
                        continue
                j += 1
            ocr_arr[i] = box1
            i += 1

        # 找出同一列中饮片最大x坐标，最大y坐标和最小坐标
        for arr in ocr_arr:
            result = '{}spl'.format(arr[1][0])
            herbal_jl = find_numbers(result)
            if herbal_jl is not None and len(herbal_jl) < 3:
                bit_len = max(bit_len, len(herbal_jl))

            flag, text = toolsutil.filter_contain_char(arr[1][0])
            if flag:
                if not toolsutil.find_opt_in_arr(arr[1][0]):
                    continue

            if max_x1 == 0:
                max_x1 = max(arr[0][2][0], arr[0][1][0])  # 最大x坐标位置
                max_y1 = min(arr[0][2][1], arr[0][3][1])  # 最大y坐标位置
                if max_y1 < 60:  # 判断如果是第一行饮片的位置
                    min_y1 = max_y1 - 35  # 右下角点的y坐标减去饮片文字行高
                elif max_y1 < 95:  # 判断如果是第二行饮片的位置
                    min_y1 = max_y1 - 63  # 右下角点的y坐标减去饮片文字行高
                elif max_y1 < 130:  # 判断如果是第三行饮片的位置
                    min_y1 = max_y1 - 98  # 右下角点的y坐标减去饮片文字行高
            else:
                new_max = max(arr[0][2][0], arr[0][1][0])  # 最大x坐标位置
                max_x1 = max(max_x1, new_max)  # 获取最大x坐标位置

    return int(max_x1), int(min_y1), bit_len, ocr_arr


def draw_rectangles(img, white_bg, max_x1, min_y1, bit_len1, qx_bit):
    """
       绘制饮片名和剂量的图片到新图片中
    """
    max_y1 = 330
    print('max_x1, min_y1, bit_len1, qx_bit', max_x1, min_y1, bit_len1, qx_bit)
    min_y1 = 3
    if bit_len1 == 2:  # 饮片剂量最大是两位数是，生成坐标位置
        if max_x1 < 142:
            tlc_x = 0 - qx_bit
        else:
            tlc_x = max_x1 - 142 - qx_bit

        tl_corner = (tlc_x, min_y1)  # 生成饮片名的左上角点位置
        br_corner = (max_x1 - 32, max_y1)  # 生成饮片名的左上角点位置

        lt_jl = (max_x1 - 33 + qx_bit, min_y1)  # 生成饮片剂量的左上角点位置
        br_jl = (max_x1 + 5, max_y1)  # 生成饮片剂量的左上角点位置
    else:
        if max_x1 < 142:
            tlc_x = 0 - qx_bit
        else:
            tlc_x = max_x1 - 142 - qx_bit

        tl_corner = (tlc_x, min_y1)  # 生成饮片名的左上角点位置
        br_corner = (max_x1 - 15, max_y1)  # 生成饮片名的左上角点位置

        lt_jl = (max_x1 - 25 + qx_bit, min_y1)  # 生成饮片剂量的左上角点位置
        br_jl = (max_x1 + 10, max_y1)  # 生成饮片剂量的左上角点位置

    herbal_image = img[tl_corner[1]:br_corner[1], tl_corner[0]:br_corner[0]]
    white_bg[tl_corner[1] + 7:br_corner[1] + 7, tl_corner[0] + qx_bit:br_corner[0] + qx_bit] = herbal_image

    small_image = img[lt_jl[1]:br_jl[1], lt_jl[0]:br_jl[0]]
    white_bg[lt_jl[1]:br_jl[1], lt_jl[0]:br_jl[0]] = small_image


def analysis_recipel(dis_img, file_path, py_x):
    """
       解析处方信息
    """
    img, cropped_image_yz = crop_img(dis_img, py_x)  # 裁剪
    file = file_path + '/recipel_img_herbal.jpg'
    cv2.imencode('.jpg', img)[1].tofile(file)
    cv2.imencode('.jpg', img)[1].tofile(file.replace('.jpg', '_c.jpg'))

    ocr_url = '{}?file={}'.format(toolsutil.ocr_server_url, file)
    content_result = toolsutil.get_request(ocr_url)

    new_img = img.copy()
    if content_result.get('status') == '200':
        position = content_result.get('position')
        if position != [None]:
            ocr_p_arr1, ocr_p_arr2, ocr_p_arr3, ocr_p_arr4 = [], [], [], []
            p_max_y = 0
            for idx in range(len(position)):  # 遍历position
                res = position[idx]
                print(res)
                for line in res:
                    max_x = max(line[0][0][0], line[0][1][0], line[0][2][0], line[0][3][0])
                    min_x = min(line[0][0][0], line[0][1][0], line[0][2][0], line[0][3][0])

                    max_y = max(line[0][0][1], line[0][1][1], line[0][2][1], line[0][3][1])
                    min_y = min(line[0][0][1], line[0][1][1], line[0][2][1], line[0][3][1])


                    p_name = line[1][0]
                    result_num = find_numbers(p_name)
                    if result_num is None:
                        if max_x - min_x < 50:
                            continue
                    else:
                        if p_name.split(result_num)[0] == '':  # 判断饮片名和剂量分开,坐标需要增加半个字符长度
                            line[0][1][0] = line[0][1][0] + 5
                            line[0][2][0] = line[0][2][0] + 5

                    if max_y - min_y > 45:
                        continue

                    if p_max_y == 0:
                        p_max_y = min_y
                    elif min_y > (p_max_y + 45):
                        break
                    else:
                        p_max_y = min_y

                    if max_x > 100:
                        if float(line[1][1]) < 0.8:
                            continue
                        if max_x < 200:
                            ocr_p_arr1.append(line)
                        elif max_x < 400:
                            ocr_p_arr2.append(line)
                        elif max_x < 600:
                            ocr_p_arr3.append(line)
                        else:
                            ocr_p_arr4.append(line)

            #             cv2.rectangle(new_img, (int(min_x), int(min_y)), (int(max_x), int(max_y)), (255, 255, 255), 1)
            #
            # cv2.namedWindow('new_img', 0)
            # cv2.imshow('new_img', new_img)
            # cv2.waitKey(0)

            max_x1, min_y1, bit_len1, ocr_p_arr1 = rectMerge(ocr_p_arr1)
            max_x2, min_y2, bit_len2, ocr_p_arr2 = rectMerge(ocr_p_arr2)
            max_x3, min_y3, bit_len3, ocr_p_arr3 = rectMerge(ocr_p_arr3)
            max_x4, min_y4, bit_len4, ocr_p_arr4 = rectMerge(ocr_p_arr4)

            qx_bit = 0
            # 如果饮片信息不存在，从前一个饮片位置信息推算
            if max_x2 == 0:
                max_x2, bit_len2 = count_herbal_width(max_x1, bit_len1)
            if max_x3 == 0:
                max_x3, bit_len3 = count_herbal_width(max_x2, bit_len2)
            if max_x4 == 0:
                max_x4, bit_len4 = count_herbal_width(max_x3, bit_len3)

            if max_x1 == 0 and max_x2 != 0:
                max_x1 = max_x2 - 191
                bit_len1 = bit_len2

            img_h, img_w = img.shape[:2]
            yz_h, yz_w = cropped_image_yz.shape[:2]
            white_bg = np.ones((img_h + yz_h, max(img_w, yz_w), 3), dtype=np.uint8) * 255

            draw_rectangles(img, white_bg, max_x1, min_y1, bit_len1, qx_bit)
            draw_rectangles(img, white_bg, max_x2, min_y2, bit_len2, qx_bit)
            draw_rectangles(img, white_bg, max_x3, min_y3, bit_len3, qx_bit)
            draw_rectangles(img, white_bg, max_x4, min_y4, bit_len4, qx_bit)

            white_bg[img_h:img_h + yz_h, 0:yz_w] = cropped_image_yz
            # cv2.rectangle(white_bg, (430, 320), (750, 360), (255, 255, 255), -1)
            cv2.imencode('.jpg', white_bg)[1].tofile(file)
            content_result = toolsutil.get_request(ocr_url)
            if content_result.get('status') == '200':
                # cv2.namedWindow('white_bg', 0)
                # cv2.imshow('white_bg', img)
                # cv2.waitKey(0)
                # cv2.destroyAllWindows()
                return get_herbal_sort(content_result, img_h, ocr_p_arr1, ocr_p_arr2, ocr_p_arr3, ocr_p_arr4, white_bg)
        return None, None
    return None, None


def draw(img, point, thickness=1):
    cv2.line(img, tuple(point[0]), tuple(point[1]), (255, 0, 255), thickness)


def get_herbal_sort(content_result, img_h, ocr_p_arr1, ocr_p_arr2, ocr_p_arr3, ocr_p_arr4, white_bg):
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
                if line[0][2][1] >= img_h:
                    if float(line[1][1]) < 0.8:
                        continue
                    reciple_arr.append(line[1][0])
                else:
                    max_x = max(line[0][0][0], line[0][1][0], line[0][2][0], line[0][3][0])
                    min_x = min(line[0][0][0], line[0][1][0], line[0][2][0], line[0][3][0])

                    if not filter_char(line[1][0]):  # 判断文本是否是饮片操作方式
                        pass
                    elif max_x - min_x < 45:  # 过滤掉手写文字
                        continue
                    max_y = max(line[0][0][1], line[0][1][1], line[0][2][1], line[0][3][1])
                    min_y = min(line[0][0][1], line[0][1][1], line[0][2][1], line[0][3][1])
                    if max_y - min_y > 35:
                        continue
                    if max_x > 100:
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

        ocr_arr1 = merge_ocr_p(ocr_arr1)
        ocr_arr2 = merge_ocr_p(ocr_arr2)
        ocr_arr3 = merge_ocr_p(ocr_arr3)
        ocr_arr4 = merge_ocr_p(ocr_arr4)

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
        min_all_y = min(max_arr)
        if max_all_y - min_all_y > 20:
            min_all_y = min_all_y + 10

        len_r = max(len1, len2, len3, len4)
        for i in range(len_r):
            min_y = (i - 0) * 36 + min_all_y
            # 取第一列饮片数据
            ocr_json_obj1, ocr_arr1, y1 = get_ocr_arr_p(ocr_arr1, min_y)
            ocr_p_json_obj1, ocr_p_arr1, y11 = get_ocr_arr_p(ocr_p_arr1, min_y)
            result.append(set_ocr_arr_val(ocr_json_obj1, ocr_p_json_obj1))

            # 取第二列饮片数据
            ocr_json_obj2, ocr_arr2, y2 = get_ocr_arr_p(ocr_arr2, min_y)
            ocr_p_json_obj2, ocr_p_arr2, y22 = get_ocr_arr_p(ocr_p_arr2, min_y)
            result.append(set_ocr_arr_val(ocr_json_obj2, ocr_p_json_obj2))

            # 取第三列饮片数据
            ocr_json_obj3, ocr_arr3, y3 = get_ocr_arr_p(ocr_arr3, min_y)
            ocr_p_json_obj3, ocr_p_arr3, y33 = get_ocr_arr_p(ocr_p_arr3, min_y)
            result.append(set_ocr_arr_val(ocr_json_obj3, ocr_p_json_obj3))

            # 取第四列饮片数据
            ocr_json_obj4, ocr_arr4, y4 = get_ocr_arr_p(ocr_arr4, min_y)
            ocr_p_json_obj4, ocr_p_arr4, y44 = get_ocr_arr_p(ocr_p_arr4, min_y)
            result.append(set_ocr_arr_val(ocr_json_obj4, ocr_p_json_obj4))

    return 'spl'.join(map(str, result)), 'spl'.join(map(str, reciple_arr))


def set_ocr_arr_val(ocr_json_obj, ocr_p_json_obj):
    if ocr_json_obj is None and ocr_p_json_obj is None:
        return '空无0g'
    else:
        new_name = ocr_json_obj
        h_name = ocr_p_json_obj
        if new_name is None:
            result_name = h_name
        else:
            if h_name is not None:
                if len(h_name) >= len(new_name) and h_name.endswith('g'):
                    result_name = h_name
                else:
                    result_name = new_name
            else:
                result_name = new_name

        result_name = '{}spl'.format(result_name)
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


def find_replace_p(ocr_rp_arr, line):
    """
       根据饮片位置信息，判断同一个位置饮片信息是否合规，不合规则替换掉，合规则添加到列饮片的列表中
    """
    flag_p = True
    if len(ocr_rp_arr) > 0:
        max_y = max(line[0][2][1], line[0][3][1])
        max_x = max(line[0][1][0], line[0][2][0])
        min_x = max(line[0][0][0], line[0][3][0])
        for i in range(len(ocr_rp_arr)):
            ocr_rp = ocr_rp_arr[i]
            max_p_y = max(ocr_rp[0][2][1], ocr_rp[0][3][1])
            max_p_x = max(ocr_rp[0][1][0], ocr_rp[0][2][0])
            min_p_x = max(ocr_rp[0][0][0], ocr_rp[0][3][0])
            if -20 < max_y - max_p_y < 20:
                flag_p = False
                if (max_x - min_x) > (max_p_x - min_p_x):
                    ocr_rp_arr[i] = line
                    break
    if flag_p:
        ocr_rp_arr.append(line)
    return ocr_rp_arr


def find_p(ocr_p_arr, line):
    """
       根据当前饮片位置信息，获取初始获取的饮片名位置信息
    """
    max_y = max(line[0][2][1], line[0][3][1])
    for ocr_p in ocr_p_arr:
        max_p_y = max(ocr_p[0][2][1], ocr_p[0][3][1])
        if -20 < max_y - max_p_y < 20:
            return ocr_p[1][0]
    return None


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

            content_recipel = "{}{}".format(recipel_no_time, recipel_no)  # 拼接处方号，对接his系统用
            content_recipel = content_recipel.replace('-', '')
            return content, recipel_img, content_yz, '', {"diagnose": "", "bar_code": content_recipel,
                                                          "receipel_no": recipel_no}
    except Exception as e:
        print(e)
    return '', None, None, None, None


def parse_ocr_texts_to_yinpian(texts):
    result = []
    noise_keywords = [
        "每日",
        "医师",
        "处方",
        "打印",
        "审核",
        "调配",
        "核对",
        "发药",
        "药品",
        "药师",
        "过敏",
        "姓名",
        "性别",
        "年龄",
        "病历",
        "诊断",
    ]
    for text in texts:
        if any(keyword in text for keyword in noise_keywords):
            continue

        match = re.search(r"(?P<name>[\u4e00-\u9fa5]+)(?P<digit>\d+(?:\.\d+)?)(?P<unit>g|克)?", text, re.I)
        if not match:
            continue

        if match.group("name") in {"张义松", "水煎取汁"}:
            continue

        result.append(
            {
                "name": match.group("name"),
                "digit_des": match.group("digit"),
                "unit": match.group("unit") or "g",
                "opt_type": "",
            }
        )
    return result


def run_demo(image_path=None):
    image_path = Path(image_path or Path(__file__).with_name("chufang2_cut.jpg"))
    print("step_ocr_task 演示图片:", image_path)
    texts = ocr_image(image_path)
    yinpian_data = parse_ocr_texts_to_yinpian(texts)

    print("识别出的饮片信息:")
    for item in yinpian_data:
        print("{name}{digit_des}{unit}{opt_type}".format(**item))

    return yinpian_data


if __name__ == '__main__':
    file_path = '{}/recipel_img.jpg'.format(toolsutil.localDir)
    recipel_img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
    if recipel_img is not None and 600 < recipel_img.shape[0] < 830:
        herbal_content, dis_img, yz_content, base_content, recipel_obj = read_chufang_content(recipel_img, toolsutil.localDir)
        print("herbal_content", herbal_content)
        herbal_json = toolsutil.get_herbal_json(herbal_content)
        print(herbal_json)

        taboo_results = toolsutil.get_taboos(herbal_json)
        print(taboo_results)
