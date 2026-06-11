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
       裁剪图片中的饮片和处方剂数信息图片
    """
    dis_img_h, dis_img_w = dis_img.shape[:2]
    # 截取处方饮片内容
    x, y, w, h = 270 + py_x, 170, dis_img_w - 270, 330
    cropped_image = dis_img[y:y + h, x:x + w]

    # 截取处方剂数内容
    x_yz, y_yz, w_yz, h_yz = 270 + py_x, 500, dis_img_w - 270, dis_img_h-500
    cropped_image_yz = dis_img[y_yz:y_yz + h_yz, x_yz:x_yz + w_yz]
    return cropped_image, cropped_image_yz


def read_chufang_content(recipel_img, file_path):
    """
       读取处方文字信息
    """
    ocr_url = '{}?file={}'.format(toolsutil.ocr_server_url, file_path)
    print(ocr_url)
    content_result = toolsutil.get_request(ocr_url)
    print(content_result)
    new_img = recipel_img.copy()
    if content_result.get('status') == '200':
        position = content_result.get('position')
        if position != [None]:
            for idx in range(len(position)):  # 遍历position
                res = position[idx]
                print(res)  # 输出识别结果
                for line in res:
                    max_x = max(line[0][0][0], line[0][1][0], line[0][2][0], line[0][3][0])
                    min_x = min(line[0][0][0], line[0][1][0], line[0][2][0], line[0][3][0])

                    max_y = max(line[0][0][1], line[0][1][1], line[0][2][1], line[0][3][1])
                    min_y = min(line[0][0][1], line[0][1][1], line[0][2][1], line[0][3][1])

                    cv2.rectangle(new_img, (int(min_x), int(min_y)), (int(max_x), int(max_y)), (255, 0, 255), 1)

    return new_img

def read_chufang_content2(recipel_img, file_path):
    """
       读取处方文字信息
    """
    new_img = recipel_img.copy()
    success, encoded_img = cv2.imencode('.jpg', recipel_img)
    # 3. 构造请求并发送到服务器
    ocr_url = toolsutil.ocr_server_img_url
    files = {'file': ('image.jpg', encoded_img.tobytes(), 'image/jpeg')}

    content_result = toolsutil.post_file_request(ocr_url, files)
    print(content_result)
    if content_result.get('status') == '200':
        position = content_result.get('position')
        if position != [None]:
            for idx in range(len(position)):  # 遍历position
                res = position[idx]
                print(res)  # 输出识别结果
                for line in res:
                    max_x = max(line[0][0][0], line[0][1][0], line[0][2][0], line[0][3][0])
                    min_x = min(line[0][0][0], line[0][1][0], line[0][2][0], line[0][3][0])

                    max_y = max(line[0][0][1], line[0][1][1], line[0][2][1], line[0][3][1])
                    min_y = min(line[0][0][1], line[0][1][1], line[0][2][1], line[0][3][1])

                    cv2.rectangle(new_img, (int(min_x), int(min_y)), (int(max_x), int(max_y)), (255, 0, 255), 1)

    return new_img

if __name__ == '__main__':
    file_path = '{}/recipel_img.jpg'.format(toolsutil.localDir)
    recipel_img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
    if recipel_img is not None and 600 < recipel_img.shape[0] < 830:
        new_img = read_chufang_content2(recipel_img, file_path)

        cropped_image, cropped_image_yz = crop_img(recipel_img, 0)

        new_img = cv2.cvtColor(new_img, cv2.COLOR_BGR2RGB)
        plt.imshow(new_img)
        plt.show()

