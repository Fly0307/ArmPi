#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/ArmPi/')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
import cv2
import time
import Camera
import threading
# from LABConfig import *
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
from CameraCalibration.CalibrationConfig import *
import pyzbar.pyzbar as pyzbar
from math import *

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()

range_rgb = {
    'red':   (0, 0, 255),
    'blue':  (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}
placement_area = {
    'red':   (-15 + 0.5, 12 - 0.5, 1.5),
    'green': (-15 + 0.5, 6 - 0.5,  1.5),
    'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
}

__target_color = ('red')
# 设置检测颜色
def setTargetColor(target_color):
    global __target_color

    print("COLOR", target_color)
    __target_color = target_color
    return (True, ())


# 夹持器夹取时闭合的角度
servo1 = 500

# 初始位置
def initMove():
    Board.setBusServoPulse(1, servo1 - 50, 300)
    Board.setBusServoPulse(2, 500, 500)
    AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)

def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

#设置扩展板的RGB灯颜色使其跟要追踪的颜色一致
def set_rgb(color):
    if color == "red":
        Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
        Board.RGB.show()
    elif color == "green":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
        Board.RGB.show()
    elif color == "blue":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
        Board.RGB.show()
    else:
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()

count = 0
_stop = False
color_list = []
get_roi = False
__isRunning = False
detect_color = 'None'
start_pick_up = False
start_count_t1 = True
def reset():
    global _stop
    global count
    global get_roi
    global color_list
    global detect_color
    global start_pick_up
    global __target_color
    global start_count_t1

    count = 0
    _stop = False
    color_list = []
    get_roi = False
    __target_color = ("blue")
    detect_color = 'None'
    start_pick_up = False
    start_count_t1 = True

def init():
    print("ColorSorting Init")
    initMove()

def start():
    global __isRunning
    reset()
    __isRunning = True
    print("ColorSorting Start")

def stop():
    global _stop
    global __isRunning
    _stop = True
    __isRunning = False
    print("ColorSorting Stop")

def exit():
    global _stop
    global __isRunning
    _stop = True
    __isRunning = False
    print("ColorSorting Exit")

rect = None
size = (640, 480)
rotation_angle = 0
unreachable = False 
world_X, world_Y = 0, 0
def move():
    global rect
    global _stop
    global get_roi
    global unreachable
    global __isRunning
    global detect_color
    global start_pick_up
    global rotation_angle
    global world_X, world_Y
    
    #放置坐标

    while True:
        if __isRunning:        
            if detect_color != 'None' and start_pick_up:  #如果检测到方块没有移动一段时间后，开始夹取
                #移到目标位置，高度6cm, 通过返回的结果判断是否能到达指定位置
                #如果不给出运行时间参数，则自动计算，并通过结果返回
                set_rgb(detect_color)
                setBuzzer(0.1)
                result = AK.setPitchRangeMoving((placement_area[detect_color][0], placement_area[detect_color][1], 7), -90, -90, 0)
                if result == False:
                    unreachable = True
                else:
                    unreachable = False
                    time.sleep(result[2]/1000) #如果可以到达指定位置，则获取运行时间

                    if not __isRunning:
                        continue
                    servo2_angle = getAngle(placement_area[detect_color][0], placement_area[detect_color][1], rotation_angle) #计算夹持器需要旋转的角度
#                     print((placement_area[detect_color][0], placement_area[detect_color][1])
                    Board.setBusServoPulse(1, servo1 - 280, 500)  # 爪子张开
                    Board.setBusServoPulse(2, servo2_angle, 500)
                    time.sleep(0.5)
                    
                    if not __isRunning:
                        continue
                    AK.setPitchRangeMoving((placement_area[detect_color][0], placement_area[detect_color][1], 1.5), -90, -90, 0, 1000)
                    time.sleep(1.5)

                    if not __isRunning:
                        continue
                    Board.setBusServoPulse(1, servo1, 500)  #夹持器闭合
                    time.sleep(0.8)

                    if not __isRunning:
                        continue
                    Board.setBusServoPulse(2, 500, 500)
                    AK.setPitchRangeMoving((placement_area[detect_color][0], placement_area[detect_color][1], 12), -90, -90, 0, 1000)  #机械臂抬起
                    time.sleep(1)

                    if not __isRunning:
                        continue
                    result = AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0)   
#                     print(result)
#                     print(result[2])
                    time.sleep(result[2]/1000)
                    
                    if not __isRunning:
                        continue                   
                    servo2_angle = getAngle(coordinate[detect_color][0], coordinate[detect_color][1], -90)
                    Board.setBusServoPulse(2, servo2_angle, 500)
                    time.sleep(0.5)

                    if not __isRunning:
                        continue
                    AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], coordinate[detect_color][2] + 3), -90, -90, 0, 500)
                    time.sleep(0.5)
                    
                    if not __isRunning:
                        continue                    
                    AK.setPitchRangeMoving((coordinate[detect_color]), -90, -90, 0, 1000)
                    time.sleep(0.8)

                    if not __isRunning:
                        continue
                    Board.setBusServoPulse(1, servo1 - 200, 500)  # 爪子张开  ，放下物体
                    time.sleep(0.8)

                    if not __isRunning:
                        continue
                    AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0, 800)
                    time.sleep(0.8)

                    initMove()  # 回到初始位置
                    time.sleep(1.5)

                    detect_color = 'None'
                    get_roi = False
                    start_pick_up = False
                    set_rgb(detect_color)
        else:
            if _stop:
                _stop = False
                Board.setBusServoPulse(1, servo1 - 70, 300)
                time.sleep(0.5)
                Board.setBusServoPulse(2, 500, 500)
                AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)
                time.sleep(1.5)
            time.sleep(0.01)
          
#运行子线程
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()    


#
def detect(image):
    # 读取图像并将其转化为灰度图片
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 计算图像中x和y方向的Scharr梯度幅值表示
    ddepth = cv2.CV_32F
    gradX = cv2.Sobel(gray, ddepth=ddepth, dx=1, dy=0, ksize=-1)
    gradY = cv2.Sobel(gray, ddepth=ddepth, dx=0, dy=1, ksize=-1)

    # x方向的梯度减去y方向的梯度
    gradient = cv2.subtract(gradX, gradY)
    # 获取处理后的绝对值
    gradient = cv2.convertScaleAbs(gradient)

    
    # 对处理后的结果进行模糊操作
    blurred = cv2.blur(gradient, (9, 9))
    # 将其转化为二值图片
    (_, thresh) = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)
    # 构建一个掩码并将其应用在二值图片中
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    # 执行多次膨胀和腐蚀操作
    closed = cv2.erode(closed, None, iterations=4)
    closed = cv2.dilate(closed, None, iterations=4)
#     cv2.imshow("closed", closed)
    # 在二值图像中寻找轮廓, 然后根据他们的区域大小对该轮廓进行排序，保留最大的一个轮廓
    cnts = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0]
    
    if len(cnts) == 0:
        return None,None,None

    c = sorted(cnts, key=cv2.contourArea, reverse=True)[0]
    # 计算最大的轮廓的最小外接矩形
    rect = cv2.minAreaRect(c)
    box = cv2.boxPoints(rect) 
    box = np.int0(box)
#     print(box)
    
    # 以下是为了将盒子中的图像遮住防止误识别
    # 计算条形码的轮廓的最大最小的坐标值
    x_max=x_min=y_max=y_min=0
#     print(rect)
    x_min=box[0][0]
    y_min=box[0][1]
    for i in range(4):
        for j in range(2):
            if j==0:
                if box[i][j]>x_max:
                    x_max=box[i][j]
                elif box[i][j]<x_min:
                    x_min=box[i][j]
            if j==1:
                if box[i][j]>y_max:
                    y_max=box[i][j]
                elif box[i][j]<y_min:
                    y_min=box[i][j]
    black_box=[[] for i in range(4)]
    #把遮盖位置左右边界扩大根据盒子和二维码张贴位置自行调整
    x_min-=20
    x_max+=40
    # 防止操作越界
    if x_min<0:
        x_min=0
    if x_max>640:
        x_max=640
    # 计算条形码的轮廓的最大最小的坐标值
    black_box[0]=(x_min,y_max)
    black_box[1]=(x_min,0)
    black_box[2]=(x_max,0)
    black_box[3]=(x_max,y_max)
    # 提取条形码后的盒子的坐标
    black_box = np.int0(black_box)
#     print(black_box)
    return box,rect,black_box

def angle(a,R=10):
    x=0.0
    y=0.0
    if  a>=0 and a <=180:
        if a==0:
            x=R
            y=0.0
            return x,y
        elif a == 90:
            x=0
            y=R
            return x,y
        elif a==180:
            x=-R
            y=0.0
            return x,y
        else:
            y= sin(pi/180*a)*R
            x= y/tan(pi/180*a)
            return x,y
    else:
        pass

def decodeDisplay(image):
    barcodes = pyzbar.decode(image)
    data=[]
    for barcode in barcodes:
        # 提取条形码的边界框的位置
        # 画出图像中条形码的边界框
        (x, y, w, h) = barcode.rect
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
 
        # 条形码数据为字节对象，所以如果我们想在输出图像上
        # 画出来，就需要先将它转换成字符串
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
 
        # 绘出图像上条形码的数据和条形码类型
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    .5, (0, 0, 125), 2)
        
        # 向终端打印条形码数据和条形码类型
        print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
        
        data.append([x,y,w,h,barcodeData])
        print(data[0][4])
    return image,data

def find_bar_code(box,rect,frame,data):
    box1=[0,0,0]
    x_max=x_min=y_max=y_min=0
    x,y=angle(abs(rect[2]),rect[1][1])
    box1=[x+rect[0][0],y+rect[0][1],'']
#     print(rect)
    x_min=box[0][0]
    y_min=box[0][1]
    for i in range(4):
        for j in range(2):
            if j==0:
                if box[i][j]>x_max:
                    x_max=box[i][j]
                elif box[i][j]<x_min:
                    x_min=box[i][j]
            if j==1:
                if box[i][j]>y_max:
                    y_max=box[i][j]
                elif box[i][j]<y_min:
                    y_min=box[i][j]
    # print(b1.shape)
    if len(data) != 0:
        box1[2]=data[0][4]
        # print(box1)

    return box1

coordinate = {
    'red':   (-15 + 0.5, 12 - 0.5, 1.5),
    'green': (-15 + 0.5, 6 - 0.5,  1.5),
    'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
}
# if __isRunning:        
#     if detect_color != 'None' and start_pick_up:  #如果检测到方块没有移动一段时间后，开始夹取

if __name__ == '__main__':
    init()
    start()
    my_camera = Camera.Camera()
    my_camera.camera_open()
    while True:
        frame = my_camera.frame
        if frame is not None:
            img = frame.copy()
            # 检测图像中的二维码内容,仅限一个
            img,data=decodeDisplay(img)
            # 计算出条形码的位置和盒子位置
#             box,rect,black_box = detect(img)
#             if rect is not None:
#                 # print(rect)
#                 if box is not None:
#                     # 框出条形码部分
#                     cv2.drawContours(frame, [box], -1, (0, 255, 0), 2)
#                     # 把条形码后的盒子部分遮住防止误识别
#                     cv2.drawContours(img, [black_box], -1, (0, 0, 0), -1)
#                     cv2.imshow('img',img)
#                     if len(data) != 0:

#                         text = data[0][4]
#                         cv2.putText(frame, text, (data[0][0], data[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX,
#                                     .5, (0, 0, 125), 2)
#                         xx, yy = convertCoordinate(data[0][0], data[0][1], size)
# #                         print(xx,yy)
#                         # 检测到特定条形码内容时才会抓取
#                         if data[0][4]=='water':
#                             detect_color = ('blue')
#                             start_pick_up=True
#                             coordinate['blue'] = (xx+2, yy+5, 12) 
#                         elif data[0][4]=='meat':
#                             detect_color = ('red')
#                             start_pick_up=True
#                             coordinate['red'] = (xx+2, yy+5, 12) 
#                         elif data[0][4]=='fruits':
#                             detect_color = ('green')
#                             start_pick_up=True
#                             coordinate['green'] = (xx+2, yy+5, 12) 
#                         else:
#                             detect_color = ('')

#                     else:
#                         __target_color = ('')

            # img = run(img)           
            cv2.imshow('frame', frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
    my_camera.camera_close()
    cv2.destroyAllWindows()
