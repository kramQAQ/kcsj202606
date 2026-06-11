import gxipy as gx


class Camera:
    def __init__(self, parent):
        self._parent = parent
        self.cam = None
        self.callback = False
        # 连接状态，取决于：打开相机、关闭相机
        self.cam_connect_status = 0
        # 运行状态，取决于：开启图像、停止图像
        self.cam_run_status = 0
        self.cam_flag = True  # 是否显示图像
        self.open_cam_device()

    # 相机设备是否准备就绪
    def is_cam_ready(self):
        return self.cam is not None and self.cam_connect_status == 1

    # 相机设备是否正在运行
    def is_cam_run(self):
        return self.cam is not None and self.cam_run_status == 1

    def open_cam_device(self):
        if not self.is_cam_ready():
            try:
                self.device_manager = gx.DeviceManager()
                self.dev_num, self.dev_info_list = self.device_manager.update_device_list()
                if self.dev_num > 0:
                    str_sn = self.dev_info_list[0].get("sn")
                    if str_sn is not None and str_sn != "":
                        self.cam = self.device_manager.open_device_by_sn(str_sn)
                        self.cam.data_stream[0].StreamBufferHandlingMode.set(gx.GxDSStreamBufferHandlingModeEntry.NEWEST_ONLY)
                        self.cam_connect_status = 1
                    else:
                        text = '相机未识别，请检查相机设备是否正常。'
                        self.show_error(text)
                else:
                    text = '相机未识别，请检查相机设备是否正常。'
                    self.show_error(text)
            except Exception as e:
                text = '相机未识别，请检查相机设备是否正常。'
                self.show_error(text)

    def show_error(self, text):
        if self._parent is not None:
            self._parent.label_text.config(text=text)
        else:
            print(text)

    def start_acquisition(self):
        if self.is_cam_ready():
            try:
                if not self.is_cam_run():
                    # 图像采集持续回调函数
                    # 注：此回调函数不能在主类里定义，否则，会报出如下错误：
                    # DataStream.register_capture_callback: Expected callback type is function not <class 'method'>
                    # 此回调函数也不能通过 partial(capture_callback, main_window=self) 封装参数的方式来调用，否则，会报出如下错误：
                    # DataStream.register_capture_callback: Expected callback type is function not <class 'functools.partial'>
                    # 所以，此回调函数只能以非常普通的方式定义在函数内部，才能正常使用。
                    def capture_callback(raw_image):
                        rgb_image = raw_image.convert("RGB")
                        # 使用原始图像中的数据创建numpy数组
                        numpy_image = rgb_image.get_numpy_array()
                        # 存储当前的帧数据，为拍照准备数据
                        self._parent.set_img(numpy_image)

                    # 注册回调函数
                    # Register capture callback (Notice: Linux USB2 SDK does not support register_capture_callback)
                    if self.callback:
                        self.cam.data_stream[0].register_capture_callback(capture_callback)
                    # 开始采集
                    self.cam.stream_on()
                    self.cam_run_status = 1
            except Exception as e:
                print(e)
                self.cam_run_status = 0
        else:
            print("[开启图像] 设备已关闭！")

    def getImg(self):
        if self.cam is not None and self.cam_run_status == 1:
            raw_image = self.cam.data_stream[0].get_image()
            rgb_image = raw_image.convert("RGB")
            # 使用原始图像中的数据创建numpy数组
            numpy_image = rgb_image.get_numpy_array()
            return numpy_image


    # 关闭工业相机设备
    def close_cam_device(self):
        if self.is_cam_ready():
            try:
                # 停止图像
                self.stop_acquisition()
                # 关闭设备
                self.cam.close_device()
                self.cam = None
                self.cam_connect_status = 0
                print("[关闭相机] 已成功关闭相机。")
            except Exception as e:
                print(e)
                self.cam = None
                self.cam_connect_status = 0
        else:
            print("[关闭相机] 当前未打开相机！")

    # 停止图像
    def stop_acquisition(self):
        if self.is_cam_ready():
            try:
                if self.is_cam_run():
                    # 停止采集
                    self.cam.stream_off()
                    # 解绑回调函数的注册
                    self.cam.data_stream[0].unregister_capture_callback()
                    print("[停止图像] 已成功停止图像。")
                else:
                    print("[停止图像] 当前未开启图像！")
            except Exception as e:
                print(e)
            self.cam_run_status = 0
        else:
            print("[停止图像] 设备已关闭！")


def getImg():
    '''
        获取相机拍照图片
    '''
    device_manager = gx.DeviceManager()
    dev_num, dev_info_list = device_manager.update_device_list()
    if dev_num == 0:
        return None
    cam = device_manager.open_device_by_index(1)  # open the first device
    # exit when the camera is a mono camera
    if cam.PixelColorFilter.is_implemented() is False:
        cam.close_device()
        return None
    cam.stream_on()
    num = 5
    for i in range(num):
        raw_image = cam.data_stream[0].get_image()
        if raw_image is None:
            continue
        rgb_image = raw_image.convert("RGB")
        if rgb_image is None:
            continue
        img = rgb_image.get_numpy_array()
        if img is not None:
            break
    cam.stream_off()
    cam.close_device()
    return img
