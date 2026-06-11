# -*- coding:UTF-8 -*-
import os
from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
import numpy as np
import cv2
app = Flask(__name__)
# 初始化ocr模型
paddle_ocr = PaddleOCR(use_angle_cls=True, lang="ch", ocr_version='PP-OCRv4', show_log=False, use_gpu=True)
@app.route('/ocr_img', methods=["POST"])
def ocr_img():
    if 'file' not in request.files:
        return jsonify(status='201', msg="未上传文件")

    file = request.files['file']
    img_bytes = file.read()

    # 将字节流高效解码为 OpenCV (NumPy) 图像格式
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify(status='201', msg="图像解码失败")

    content = ''
    result_arr = []
    result = paddle_ocr.ocr(img, cls=True)
    if result != [None]:
        for idx in range(len(result)):  # 遍历result
            res = result[idx]
            for line in res:
                result_tuple = eval("(" + str(line[1]) + ")")
                content += str(result_tuple[0]) + 'spl'  # 文本内容用特殊字符串标记处理

        content = content.replace(" ", "")  # 去除掉空格内容
        content = content.replace(":", "").replace("：", "")  # 去除掉中英文冒号
    result_arr.append(content)
    return jsonify(status='200', result=result_arr, position=result)

@app.route('/ocr_filepath', methods=["POST", "GET"])
def ocr_filepath():
    '''
        发送识别图片地址进行文字识别
    '''
    # 获取请求参数的内容址
    file = request.args.get("file", '')
    print(file)
    result_arr = []
    if os.path.exists(file):
        result = paddle_ocr.ocr(file, cls=True)
        content = ''
        if result != [None]:
            for idx in range(len(result)):  # 遍历result
                res = result[idx]
                for line in res:
                    result_tuple = eval("(" + str(line[1]) + ")")
                    content += str(result_tuple[0]) + 'spl'  # 文本内容用特殊字符串标记处理

            content = content.replace(" ", "")  # 去除掉空格内容
            content = content.replace(":", "").replace("：", "") # 去除掉中英文冒号
        result_arr.append(content)
        return jsonify(status='200', result=result_arr, position=result)
    else:
        return jsonify(status='201', msg="文件不存在")


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=False, debug=False, port=8866)