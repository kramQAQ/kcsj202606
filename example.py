import cv2,datetime,os
from tkinter import *
from PIL import Image, ImageTk
import camera
class collection_data:
    def __init__(self, master=None):
        self.root = master
        width = 800
        height = 700
        x = self.root.winfo_screenwidth() // 2 - width // 2
        y = self.root.winfo_screenheight() // 2 - height // 2
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        self.root.resizable(0, 0)  # 窗体大小不可调
        self.root.title('饮片数据采集')
        self.frm1 = Frame(self.root, bg='#222426', height=40, width=800)
        self.frm1.place(x=0, y=5)
        self.frm2 = Frame(self.root, bg='#ECF0F3', height=660, width=800)
        self.frm2.place(x=0, y=45)
        self.img = None
        self.cam_flag = False
        self.image_label = None
        self.confrim_button = None
        self.label_text = None
        self.data_folder_train = 'D://dataset/'
        self.label_folder_train = 'D://dataset/label'

        self.create_page()

        self.camera = camera.Camera(self)
        self.camera.start_acquisition()

        self.start()

    def create_page(self):
        Label(self.frm1, text='饮片数据采集', bg='#222426', fg='#ffffff',anchor="w",
              font='Verdana 12 bold').place(x=20,width="600", height='40')
        Button(self.frm1, text='退出', bg="#3e4043", fg="#ffffff", font='Verdana 11',
               cursor='hand2', border="0", command=self.on_close).place(x=700, y=0, height='40', width=100)

        # 显示图片标签
        self.image_label = Label(self.frm2, bg='#e1e1e1')
        self.image_label.place(x=40, y=10, height=512, width=700)

        images = Image.open('ScreenShot.png')
        w, h = images.size
        pil_image_resized = self.img_resize(w, h, 612, 512, images)
        photo = ImageTk.PhotoImage(pil_image_resized)

        self.image_label.configure(image=photo)
        self.image_label.image = photo

        # 保存按钮
        self.confrim_button = Button(self.frm2, bg="#0066FF", fg="#ffffff", font='9', border="0", cursor='hand2')
        self.confrim_button.place(x=40, y=590, height='40', width=110)
        self.confrim_button.config(text='保存', command=lambda: self.save_img())

        #  提示信息标签
        self.label_text = Label(self.frm2, bg='#ECF0F3', fg='#000000', font='9', height='30', anchor="w")
        self.label_text.place(x=40, y=540, height=30, width=700)
        self.label_text.config(text='饮片采集数据存放位置')

    def save_img(self):
        if self.img is not None:
            if not os.path.exists(self.data_folder_train):
                os.makedirs(self.data_folder_train)
                os.makedirs(self.label_folder_train)
            today = datetime.datetime.now()
            file_name = today.strftime("%m%d_%H%M%S")
            new_img = cv2.cvtColor(self.img, cv2.COLOR_RGB2BGR)  # 将RGB格式图片转换成BGR格式
            cv2.imwrite(f"{self.data_folder_train}/{file_name}.jpg", new_img)  # 保存饮片图片

    def start(self):
        self.cam_flag = True
        self.set_img()  # 开始显示图片

    def set_img(self):
        while self.cam_flag:
            self.img = self.camera.getImg()
            if self.img is not None:
                images = Image.fromarray(self.img)  # 从数组到图像？
                w, h = images.size
                pil_image_resized = self.img_resize(w, h, 612, 512, images)
                photo = ImageTk.PhotoImage(pil_image_resized)
                self.image_label.configure(image=photo)
                self.image_label.image = photo
                self.root.update()
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
        self.root.destroy()

if __name__ == '__main__':
    root = Tk()
    collection_data(root)
    root.mainloop()

# E:\homework\2026\kcsj\.venv\python.exe E:\homework\2026\kcsj\example.py