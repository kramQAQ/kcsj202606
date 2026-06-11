import requests
import re

ocr_server_url = "http://127.0.0.1:8866/ocr_filepath"

ocr_server_img_url = "http://127.0.0.1:8866/ocr_img"

localDir = 'chufang'
opt_arr = ['先煎', '后下', '分冲', '另煎', '包煎', '烊化', '冲服', '代茶饮', '样化', '先下']

# 不宜同用，十八反
not_suitable = [{"name": "草乌、川乌、附子、黑顺片、附片", "value": "贝母、半夏、白及、白蔹、天花粉、瓜蒌"},
                {"name": "藜芦", "value": "人参、党参、南沙参、苦参、红参、西洋参、玄参、丹参、北沙参、细辛、赤芍、白芍、芍药"},
                {"name": "甘草", "value": "大戟、芫花、甘遂、海藻"}, {"name": "天仙藤", "value": "牵牛子"}]

# 不宜同用，十九畏
not_suitable_fear = [{"name": "硫黄", "value": "朴硝、芒硝"}, {"name": "水银", "value": "砒霜"}, {"name": "狼毒", "value": "密陀僧"},
                     {"name": "巴豆", "value": "牵牛"}, {"name": "丁香", "value": "郁金"},{"name": "川乌、草乌", "value": "犀角"},
                     {"name": "牙硝、芒硝", "value": "三棱"}, {"name": "官桂、肉桂", "value": "石脂"},{"name": "人参", "value": "五灵脂"}]


# 过量
excessive = [{"name":"白屈菜", "value":18},{"name":"黑顺片", "value":15},{"name":"附片", "value":15},{"name":"土鳖虫", "value":10},
             {"name":"贯众", "value":10},{"name":"仙茅", "value":10},{"name":"白果", "value":10},{"name":"苍耳子", "value":10},
             {"name":"杏仁", "value":10},{"name":"蛇床子", "value":10},{"name":"蒺藜", "value":10},{"name":"蕲蛇", "value":9},
             {"name":"北豆根", "value":9},{"name":"天南星", "value":10},{"name":"半夏", "value":9},{"name":"生艾叶", "value":9},
             {"name":"艾叶炭", "value":9},{"name":"白附子", "value":6},{"name":"全蝎", "value":6},{"name":"山豆根", "value":6},
             {"name":"牵牛子", "value":6},{"name":"蜂房", "value":5},{"name":"吴茱萸", "value":5},{"name":"白花蛇", "value":5},
             {"name":"蜈蚣", "value":5},{"name":"川乌", "value":3},{"name":"草乌", "value":3},{"name":"细辛", "value":3},
             {"name":"水蛭", "value":3},{"name":"血竭", "value":2},{"name":"大皂角", "value":1.5},{"name":"水蛭面", "value":1.5},
             {"name":"白矾", "value":1.5},{"name":"朱砂", "value":0.5},{"name":"醋红大戟", "value":3},{"name":"醋商陆", "value":9},
             {"name":"川楝子", "value":10},{"name":"醋芫花", "value":3}]

# 例外
herbal_exception = ['核桃仁', '白附子', '白花蛇舌草']

# 有毒物质
toxic_material = ['砒石','红砒','白砒','砒霜','水银','生马前子','生白附子','生附子','生半夏','生南星','斑蝥','青娘虫','红娘虫',
                  '生甘遂','生狼毒','生藤黄','生千金子','闹阳花','雪上一枝蒿','红升丹','白降丹','蟾酥','洋金花','红粉','轻粉',
                  '雄黄','川乌','马钱子','天仙子','巴豆','闹羊花','草乌', '黑顺片','仙茅','天南星','使君子']


def replace_char(name):
    """
        识别错误信息替换
    """
    replacements = {"[*]": "",'[]':"",'（': '(','）':')', "：": '','·':'', ' ':'', "88": "8g", "gg": "9g", "log": "10g", "l0g": "10g",
        "og": "0g","8s": "gs","积实": "枳实","积壳":"枳壳","焊桃":"燀桃","连趣":"连翘","莱子":"莱菔子","山植":"山楂"}
    # 使用正则表达式的|操作符来匹配多个字符串，并进行替换
    pattern = '|'.join(map(re.escape, replacements.keys()))
    return re.sub(pattern, lambda m: replacements[m.group(0)], name)



def post_file_request(url, files, timeout=10):
    try:
        response = requests.post(url, files=files, timeout=timeout*3)
        print(response.status_code)
        if response.status_code == 200:
            return response.json()
        return {'status': '0'}
    except Exception as e:
        print(e)
        return {'status': '0'}

def post_request(url, json_data, timeout=10):
    try:
        response = requests.post(url, json=json_data, timeout=timeout*3)
        if response.status_code == 200:
            return response.json()
        return {'status': '0'}
    except Exception as e:
        print(e)
        return {'status': '0'}


def get_request(url, timeout=10):
    try:
        response = requests.get(url, timeout=(timeout, timeout*3))
        if response.status_code == 200:
            return response.json()
        return {'status': '0'}
    except Exception as e:
        print(e)
        return {'status': '0'}


def filter_contain_char(name):
    for opt_name in opt_arr:
        if name.count(opt_name) > 0:
            return True, opt_name
    return False, ''


def replace_end_str(content, end_str):
    content = replace_char(content)
    if content.endswith(end_str):
        content = content[:len(content)-len(end_str)]
        return replace_end_str(content, end_str)
    return content


def find_opt_in_arr(name):
    if name in opt_arr:
        return True
    return False


def find_numbers_in_string(input_string):
    result_arr = re.findall(r'\d+\.?\d{1,}', input_string)  # 先匹配小数
    if len(result_arr):
        return result_arr[len(result_arr) - 1]
    else:
        result_arr = re.findall(r'\d+', input_string)  # 匹配整数数
        if len(result_arr):
            return result_arr[len(result_arr) - 1]
    return None


def find_corners_point(approx):
    '''
       根据点坐标计算点位置
    '''
    x_arr, y_arr = [], []
    point_arr = []
    # 【数据初始化】将输入的点集解包，分别存入x、y数组和整体点数组中
    for point in approx:
        x, y = point
        point_arr.append([x, y])
        x_arr.append(x)
        y_arr.append(y)

    #  第一步：找出 X轴最小的两个点（即位于左侧的两个点：左上或左下）
    min_x = min(x_arr)
    min_x_i = x_arr.index(min_x)
    point_minx = point_arr[min_x_i]

    # 从数组中移除已找到的第一个最小X点，防止重复查找
    x_arr.remove(min_x)
    del y_arr[min_x_i]
    del point_arr[min_x_i]

    min_x2 = min(x_arr)
    min_x_i2 = x_arr.index(min_x2)
    point_minx2 = point_arr[min_x_i2]

    # 同样移除第二个最小X点
    x_arr.remove(min_x2)
    del y_arr[min_x_i2]
    del point_arr[min_x_i2]

    # 第二步：在剩余的点中找出 Y轴最小的点（即最顶部的点）
    min_y = min(y_arr)
    min_y_i = y_arr.index(min_y)
    point_miny = point_arr[min_y_i]

    # 移除该点后，point_arr 中将只剩下最后一个点（必然是右下角的点）
    y_arr.remove(min_y)
    del x_arr[min_y_i]
    del point_arr[min_y_i]

    # 第三步：核心逻辑判断，区分左上、左下、右上、右下
    if point_minx[0] <= point_minx2[0]:   # x最小: 如果第一个取出的点横坐标更小（更靠左）
        if point_minx[1] > point_minx2[1]:  # y值大
            [ltx, lty] = point_minx2  # x最大，y值小为左上
            [lbx, lby] = point_minx  # x最小，y值大为左下
        else:
            [ltx, lty] = point_minx  # x最大，y值小为左上
            [lbx, lby] = point_minx2
        [rtx, rty] = point_miny
        [rbx, rby] = point_arr[0]
    else:  # 如果第二个取出的点横坐标更小（更靠左）
        if point_minx[1] > point_minx2[1]:  # y值大
            [ltx, lty] = point_minx  # x最大，y值小为左上
            [lbx, lby] = point_minx2

        else:
            [ltx, lty] = point_minx2  # x最大，y值小为左上
            [lbx, lby] = point_minx  # x最小，y值大为左下
        [rtx, rty] = point_miny
        [rbx, rby] = point_arr[0]

    return ltx, lty, lbx, lby, rtx, rty, rbx, rby


def check_exist(name_arr, h_json):
    flag = False
    result = []
    for name in name_arr:
        for h in h_json:
            if name in h.get('name'):
                result.append(h.get('name'))
                flag = True
    return flag, '、'.join(result)


def check_not_suitable(h_json, not_suitable_json, rtype):
    results = []
    for json_obj in not_suitable_json:
        name_str = json_obj.get("name")
        name_arr = []
        if '、' in name_str:
            name_arr = name_str.split('、')
        else:
            name_arr.append(name_str)
        flag, result = check_exist(name_arr, h_json)

        value_str = json_obj.get("value")
        value_arr = []
        if '、' in value_str:
            value_arr = value_str.split('、')
        else:
            value_arr.append(value_str)

        flag_value, result_value = check_exist(value_arr, h_json)
        if flag and flag_value:
            results.append(''.join([result, '与', result_value, rtype]))
    return results


def check_pregnancy_exist(h_json,name_arr,herbal_exception):
    flag = False
    result = []
    for name in name_arr:
        for h in h_json:
            if name in h.get('name'):
                if name not in herbal_exception:
                    result.append(h.get('name'))
                    flag = True

    return flag, '、'.join(result)


def check_excessive(h_json,name_json,herbal_exception):
    flag = False
    result = []
    for nameobj in name_json:
        name = nameobj.get('name')
        for h in h_json:
            if h.get("name") not in herbal_exception:
                if name in h.get("name"):
                    if int(h.get("digit_des")) > nameobj.get('value'):
                        result.append('{}{}g(限量{}g)'.format(h.get("name"), h.get("digit_des"), nameobj.get('value')))
                        flag = True

    return flag, '、'.join(result)


def get_taboos(herbalJson):
    results = []
    results1 = check_not_suitable(herbalJson, not_suitable, '不宜同用；')
    if len(results1) > 0:
        results.append('相反饮片：'+'、'.join(results1))

    results2 = check_not_suitable(herbalJson, not_suitable_fear, '相畏；')
    if len(results2) > 0:
        results.append('相畏饮片：'+'、'.join(results2))

    flag_toxic, result_toxic = check_pregnancy_exist(herbalJson, toxic_material, herbal_exception)
    if flag_toxic:
        results.append('有毒饮片：%s；' % result_toxic)

    flag_excessive, result_excessive = check_excessive(herbalJson, excessive, herbal_exception)
    if flag_excessive:
        results.append('过量饮片：%s；' % result_excessive)
    return results


def get_herbal_json(content):
    """
        解析提取的饮片信息，形成新的json数据
    """
    herbal_arr = content.split('spl')  # 文本解析
    result_json = []
    herbal_name = ''
    for herbal in herbal_arr:
        if herbal:
            digit_des = find_numbers_in_string(herbal)  # 匹配字符中的数字，为饮片剂量
            if digit_des is not None:  # 匹配到有饮片剂量
                result_arr = herbal.split(digit_des)
                if len(result_arr) > 1:  # 匹配到有饮片名称和剂量单位
                    if result_arr[0] and result_arr[0] != 'g':
                        name = result_arr[0]
                    else:
                        name = herbal_name

                    unit = 'g'
                    if len(result_arr) > 1:
                        if 'g' in result_arr[1]:
                            unit = 'g'
                        else:
                            unit = '条'

                    opt_flag, opt_type = filter_contain_char(name)
                    if opt_flag:
                        name = name.replace(opt_type, '') # 替换掉煎药方式

                    if name == '空无':
                        result_json.append({"name": '', "digit_des": '0', "unit": unit, "opt_type": opt_type})
                    elif name is not None:  # 饮片完全匹配
                        result_json.append({"name": name, "digit_des": digit_des, "unit": unit, "opt_type": opt_type})

            else:
                herbal_name = herbal
    return result_json


if __name__ == '__main__':
    herbalJson = [{"name": '细辛', "digit_des": 4, "unit": 'g', "opt_type": ''},
                  {"name": '西洋参', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '徐长卿', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '制草乌', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '甘草片', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '半夏', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '大戟', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '硫黄', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '朴硝', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '生桃仁', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '巴豆', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '枳实', "digit_des": 5, "unit": 'g', "opt_type": ''},
                  {"name": '黑顺片', "digit_des": 5, "unit": 'g', "opt_type": ''}]

    taboo_results = get_taboos(herbalJson)
    print(taboo_results)
