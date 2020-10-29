import cv2
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np


def cvimg_to_qtimg(cvimg):
    height, width, depth = cvimg.shape
    cvimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB)
    cvimg = QImage(cvimg.data, width, height, width *
                   depth, QImage.Format_RGB888)
    return cvimg


class MyLabel(QLabel):
    mylabelSig = pyqtSignal(str)
    mylabelDoubleClickSig = pyqtSignal(str)

    def scale_init(self, scale_factor):
        self.scale_factor = scale_factor

    def updateImg(self, img):
        self.img = img.copy()
        self.point_num = 0
        self.point_list = []

    def mousePressEvent(self, e):    # 单击
        x = e.x()
        y = e.y()
        if self.point_num == 0:
            cv2.circle(self.img, (x, y), 8, (255, 0, 0), -1)
            self.point_list.append(
                [int(x/self.scale_factor), int(y/self.scale_factor)])
        if self.point_num == 1:
            cv2.circle(self.img, (x, y), 8, (0, 0, 255), -1)
            self.point_list.append(
                [int(x/self.scale_factor), int(y/self.scale_factor)])
        if self.point_num == 2:
            cv2.circle(self.img, (x, y), 8, (255, 0, 255), -1)
            self.point_list.append(
                [int(x/self.scale_factor), int(y/self.scale_factor)])
        if self.point_num == 3:
            cv2.circle(self.img, (x, y), 8, (255, 255, 0), -1)
            self.point_list.append(
                [int(x/self.scale_factor), int(y/self.scale_factor)])
        self.point_num += 1
        self.setPixmap(QPixmap(cvimg_to_qtimg(self.img)))
        sigContent = self.objectName()
        self.mylabelSig.emit(sigContent)


class window(QWidget):

    def __init__(self, img_dir, H_mat_dir, template_file, scale_factor):
        super().__init__()
        self.scale_factor = scale_factor
        self.img_list = []
        self.img_name = []
        img_list = os.listdir(img_dir)
        for i in range(len(img_list)):
            if img_list[i][-3:] == "jpg" or img_list[i][-3:] == "png":
                img_path = os.path.join(img_dir, img_list[i])
                self.img_list.append(img_path)
                self.img_name.append(img_list[i][:-4])
        self.template = cv2.imread(template_file)
        self.tp_height, self.tp_width, _ = self.template.shape
        template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
        self.template_gray = cv2.cvtColor(template_gray, cv2.COLOR_GRAY2BGR)
        self.img_original_list = []
        self.img_resized_list = []
        self.H_mat_file_list = []
        self.img_id = 0
        max_img_height = 0
        max_img_width = 0
        for i in range(len(self.img_list)):
            img_original = cv2.imread(self.img_list[i])
            image_resize = cv2.resize(
                img_original, None, fx=self.scale_factor, fy=self.scale_factor)
            height, width, _ = img_original.shape
            self.img_original_list.append(img_original)
            self.img_resized_list.append(image_resize)
            H_mat_file = self.img_name[i] + '.HMatrix'
            H_mat_path = os.path.join(H_mat_dir, H_mat_file)
            self.H_mat_file_list.append(H_mat_path)
            if max_img_height < height:
                max_img_height = height
            if max_img_width < width:
                max_img_width = width

        max_img_height = max_img_height*self.scale_factor
        max_img_width = max_img_width*self.scale_factor
        self.img_num = len(self.img_original_list)
        self.H_mat_list = [None]*self.img_num
        self.img_view_list = [None]*self.img_num

        self.label_button_height = 500
        self.label_button_width = 500
        window_height = max(max_img_height+20,
                            self.label_button_height)+self.tp_height+20
        window_width = max(
            max_img_width+20+self.label_button_width, 2*self.tp_width+40)

        self.setGeometry(10, 10, window_width, window_height)
        self.setWindowTitle('Homography Matrix Annotator')
        self.label_s = MyLabel(self)
        self.label_s.setGeometry(QRect(10, 10, max_img_width, max_img_height))
        self.label_s.setPixmap(
            QPixmap(cvimg_to_qtimg(self.img_resized_list[self.img_id])))
        self.label_s.setScaledContents(False)
        self.label_s.scale_init(self.scale_factor)
        self.label_s.updateImg(self.img_resized_list[self.img_id])
        self.label_s.setMouseTracking(True)
        self.label_t = MyLabel(self)
        self.label_t.setGeometry(QRect(10, max(
            max_img_height+20, self.label_button_height)+10, self.tp_width, self.tp_height))
        self.label_t.setPixmap(QPixmap(cvimg_to_qtimg(self.template)))
        self.label_t.scale_init(1.0)
        self.label_t.updateImg(self.template)
        self.label_t.setMouseTracking(True)
        self.label_st = QLabel(self)
        self.label_st.setGeometry(QRect(self.tp_width+30, max(
            max_img_height+20, self.label_button_height)+10, self.tp_width, self.tp_height))
        self.label_st.setPixmap(QPixmap(cvimg_to_qtimg(self.template_gray)))

        self.pushButton1 = QPushButton(self)
        self.pushButton1.setGeometry(QRect(max_img_width+70, 20, 400, 60))
        self.pushButton1.setText("Next Img")
        self.pushButton1.clicked.connect(self._down_func)
        self.pushButton2 = QPushButton(self)
        self.pushButton2.setGeometry(QRect(max_img_width+70, 120, 400, 60))
        self.pushButton2.setText("Last Img")
        self.pushButton2.clicked.connect(self._up_func)
        self.pushButton3 = QPushButton(self)
        self.pushButton3.setGeometry(QRect(max_img_width+70, 220, 400, 60))
        self.pushButton3.setText("Apply")
        self.pushButton3.clicked.connect(self._apply_func)
        self.pushButton4 = QPushButton(self)
        self.pushButton4.setGeometry(QRect(max_img_width+70, 320, 400, 60))
        self.pushButton4.setText("Clean")
        self.pushButton4.clicked.connect(self._clean_func)
        self.pushButton5 = QPushButton(self)
        self.pushButton5.setGeometry(QRect(max_img_width+70, 420, 400, 60))
        self.pushButton5.setText("Output")
        self.pushButton5.clicked.connect(self._output_func)

    def _down_func(self):
        self.img_id += 1
        if self.img_id == self.img_num:
            self.img_id = self.img_num - 1
        self.label_s.setPixmap(
            QPixmap(cvimg_to_qtimg(self.img_resized_list[self.img_id])))
        self.label_t.setPixmap(QPixmap(cvimg_to_qtimg(self.template)))
        self.label_s.updateImg(self.img_resized_list[self.img_id])
        self.label_t.updateImg(self.template)
        img_view = self.img_view_list[self.img_id]
        if img_view is not None:
            self.label_st.setPixmap(QPixmap(cvimg_to_qtimg(img_view)))
        else:
            self.label_st.setPixmap(
                QPixmap(cvimg_to_qtimg(self.template_gray)))
        print(self.H_mat_list[self.img_id])

    def _up_func(self):
        self.img_id -= 1
        if self.img_id == -1:
            self.img_id = 0
        self.label_s.setPixmap(
            QPixmap(cvimg_to_qtimg(self.img_resized_list[self.img_id])))
        self.label_t.setPixmap(QPixmap(cvimg_to_qtimg(self.template)))
        self.label_s.updateImg(self.img_resized_list[self.img_id])
        self.label_t.updateImg(self.template)
        img_view = self.img_view_list[self.img_id]
        if img_view is not None:
            self.label_st.setPixmap(QPixmap(cvimg_to_qtimg(img_view)))
        else:
            self.label_st.setPixmap(
                QPixmap(cvimg_to_qtimg(self.template_gray)))
        print(self.H_mat_list[self.img_id])

    def _apply_func(self):
        points_e = np.float32(self.label_s.point_list)
        points_l = np.float32(self.label_t.point_list)
        if len(points_e) == 4 and len(points_l) == 4:
            homographyMatrix = cv2.getPerspectiveTransform(points_e, points_l)
            self.H_mat_list[self.img_id] = homographyMatrix
            current_img = self.img_original_list[self.img_id]
            img_tran = cv2.warpPerspective(
                current_img, homographyMatrix, (self.tp_width, self.tp_height))
            img_tran_gray = cv2.cvtColor(img_tran, cv2.COLOR_BGR2GRAY)
            ret, mask = cv2.threshold(
                img_tran_gray, 10, 255, cv2.THRESH_BINARY_INV)
            img_template_gray = cv2.bitwise_and(
                self.template_gray, self.template_gray, mask=mask)
            img_view = cv2.bitwise_or(img_tran, img_template_gray)
            self.img_view_list[self.img_id] = img_view
            self.label_st.setPixmap(QPixmap(cvimg_to_qtimg(img_view)))

    def _clean_func(self):
        self.H_mat_list[self.img_id] = None
        self.img_view_list[self.img_id] = None
        self.label_s.setPixmap(
            QPixmap(cvimg_to_qtimg(self.img_resized_list[self.img_id])))
        self.label_t.setPixmap(QPixmap(cvimg_to_qtimg(self.template)))
        self.label_s.updateImg(self.img_resized_list[self.img_id])
        self.label_t.updateImg(self.template)
        self.label_st.setPixmap(QPixmap(cvimg_to_qtimg(self.template_gray)))

    def _output_func(self):
        for i in range(len(self.H_mat_file_list)):
            H_file = self.H_mat_file_list[i]
            homographyMatrix = self.H_mat_list[i]
            if homographyMatrix is None:
                continue
            f = open(H_file, 'w')
            for r in range(3):
                for c in range(3):
                    f.write(str(homographyMatrix[r][c]))
                    f.write(' ')
                f.write('\n')
            f.close()


if __name__ == '__main__':
    img_dir = sys.path[0] + '/dataset/img/'
    H_mat_dir = sys.path[0] + '/dataset/H_mat/'
    template_file = sys.path[0] + '/dataset/field_nba_new.jpg'
    scale_factor = 0.8
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    window = window(img_dir, H_mat_dir, template_file, scale_factor)
    window.show()
    sys.exit(app.exec_())
