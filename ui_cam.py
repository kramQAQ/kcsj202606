from tkinter import *
from PIL import Image, ImageFont, ImageDraw,ImageTk
import cv2,os
import camera
import requests

class collection_data:
    def __init__(self, master=None):
        self.root = master
        width = 800
        height = 700
        x = self.root.winfo_screenwidth() // 2 - width // 2
        y = self.root.winfo_screenheight() // 2 - height // 2
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        self.root.resizable(0, 0)  # 窗体大小不可调
        self.root.title('饮片目标检测')
        self.frm1 = Frame(self.root, bg='#222426', height=40, width=800)
        self.frm1.place(x=0, y=5)
        self.frm2 = Frame(self.root, bg='#ECF0F3', height=660, width=800)
        self.frm2.place(x=0, y=45)

        self.cam_flag = False
        self.confrim_button = None
        self.label_text = None
        self.image_label = None
        self.img = None
        self.previous_img = None
        self.bg = None
        self.stable_frame_arr = []
        self.static_num = 5

        self.create_page()
        self.camera = camera.Camera(self)
        self.camera.start_acquisition()

    def create_page(self):
        Label(self.frm1, text='饮片目标检测', bg='#222426', fg='#ffffff',anchor="w",
              font='Verdana 12 bold').place(x=20,width="600", height='40')
        Button(self.frm1, text='退出', bg="#3e4043", fg="#ffffff", font='Verdana 11',
               cursor='hand2',border="0", command=self.on_close).place(x=700, y=0, height='40', width=100)
        # 显示图片标签
        self.image_label = Label(self.frm2, bg='#e1e1e1')
        self.image_label.place(x=40, y=10, height=512, width=700)

        self.label_text = Label(self.frm2, bg='#ECF0F3', fg='#000000', font='9', height='30', anchor="w")
        self.label_text.place(x=40, y=540, height=30, width=700)

        # 保存按钮
        self.confrim_button = Button(self.frm2, bg="#0066FF", fg="#ffffff", font='9',border="0", cursor='hand2')
        self.confrim_button.place(x=40, y=590, height='40', width=110)
        self.confrim_button.config(text='开始检测', command=lambda: self.start())

    def start(self):
        self.cam_flag = True
        self.previous_img = None
        self.bg = None
        self.root.update()
        self.confrim_button.config(text='停止检测', command=lambda: self.stop())
        self.set_img()  #  开始显示图片

    def stop(self):
        self.cam_flag = False
        self.confrim_button.config(text='开始检测', command=lambda: self.start())

    def tesk_img(self):
        predict_image = cv2.cvtColor(self.img, cv2.COLOR_RGB2BGR)
        success, encoded_img = cv2.imencode('.jpg', predict_image)

        # 3. 构造请求并发送到服务器
        url = "http://127.0.0.1:9965/predict_img"
        files = {'file': ('image.jpg', encoded_img.tobytes(), 'image/jpeg')}
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
                yolo_result = response.json()
                if yolo_result.get('status') == '200':
                    new_img = Image.fromarray(self.img)  # 从数组到图像？
                    draw = ImageDraw.Draw(new_img)
                    boxes = yolo_result.get("result")
                    for box in boxes:
                        x1, y1, x2, y2 = box.get("bbox")
                        draw.rectangle([(x1, y1), (x2, y2)], fill=None, outline=(255, 0, 0), width=3)
                        fontText = ImageFont.truetype("font/msyhbd.ttc", 30, encoding="utf-8")
                        position_str = f'{box.get("name")} {box.get("confidence"):.2f}'
                        text_w = draw.textlength(position_str, fontText)
                        draw.rectangle((x1, y1 - 60, x1 + 30 + text_w, y1), fill=(255, 0, 0))
                        draw.text((x1 + 15, y1 - 54), position_str, text_color=(255, 255, 255), font=fontText)

                    w, h = new_img.size
                    pil_image_resized = self.img_resize(w, h, 612, 512, new_img)
                    photo = ImageTk.PhotoImage(pil_image_resized)
                    self.image_label.configure(image=photo)
                    self.image_label.image = photo
                    self.root.update()
                else:
                    print(yolo_result.get("msg"))
        except Exception as e:
            print(e)

    def set_img(self):
        while self.cam_flag is True:
            self.img = self.camera.getImg()
            if self.img is not None:
                self.tesk_img()
            else:
                break

    def img_resize(self, w, h, w_box, h_box, pil_image):
        f1 = w_box/w
        f2 = h_box/h
        factor = min(f1, f2)
        width = int(w*factor)
        height = int(h*factor)
        return pil_image.resize((width, height), Image.LANCZOS)

    def on_close(self):
        self.camera.close_cam_device()
        self.root.destroy()

if __name__ == '__main__':
    root = Tk()
    collection_data(root)
    root.mainloop()


