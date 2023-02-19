import cv2
import time
import Camera
import threading
import sys
sys.path.append('/home/pi/ArmPi/')
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
from CameraCalibration.CalibrationConfig import *
from math import *
import pyzbar.pyzbar as pyzbar
# from LABConfig import *


if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

# 调用机械臂控制函数
AK = ArmIK()

range_rgb = {
    'red':   (0, 0, 255),
    'blue':  (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}
# 放置位置,代表地址，和demo图纸不同颜色对应
# placement_area = {
#     'red':   (-15 + 0.5, 12 - 0.5, 1.5),
#     'green': (-15 + 0.5, 6 - 0.5,  1.5),
#     'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
# }
# coordinate = {
#     'red':   (-15 + 0.5, 12 - 0.5, 2),
#     'green': (-15 + 0.5, 6 - 0.5,  2),
#     'blue':  (-15 + 0.5, 0 - 0.5,  2),
# }
#坐标以机械臂底座舵机为中心
coordinate = {
        'red':   (-15 + 0.5, 6 - 0.5, 2),
        'green': (-15 + 0.5, -0 - 0.5,  2),
        'blue':  (-15 + 0.5, -6 - 0.5,  2),
    }

__target_color = ('None')
# 设置检测颜色


# 夹持器夹取时闭合的角度
servo1 = 500
# 初始位置


def initMove():
    global count
    count = {'red':   0,
    'green': 0,
    'blue':  0,}
    Board.setBusServoPulse(1, servo1 - 50, 300)
    Board.setBusServoPulse(2, 500, 500)
    AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)


def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

# 设置扩展板的RGB灯颜色使其跟要追踪的颜色一致


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


count = {'red':   0,
    'green': 0,
    'blue':  0,}  # 放置高度计数
_stop = False
color_list = []
get_roi = False
__isRunning = False
detect_color = 'None'
start_pick_up = False  # 为true时抓取方块
pick_up=False
start_pick_down = False  # 为true时放置方块，均为false时恢复初始状态
start_count_t1 = True


def reset():
    global _stop
    global count
    global get_roi
    global color_list
    global detect_color
    global start_pick_up
    global start_pick_down
    global pick_up
    global __target_color
    global start_count_t1
    global z_r, z_g, z_b, z

    count = count = {'red':   0,
    'green': 0,
    'blue':  0,} 
    _stop = False
    color_list = []
    get_roi = False
    __target_color = 'None'
    detect_color = 'None'
    start_pick_up = False
    pick_up=False
    start_pick_down = False
    start_count_t1 = True
    z_r = coordinate['red'][2]
    z_g = coordinate['green'][2]
    z_b = coordinate['blue'][2]
    z = z_r


def init():
    print("QRSorting Init")
    initMove()


def start():
    global __isRunning
    reset()
    __isRunning = True
    print("QRSorting Start")


def stop():
    global _stop
    global __isRunning
    _stop = True
    __isRunning = False
    print("QRSorting Stop")


def exit():
    global _stop
    global __isRunning
    _stop = True
    __isRunning = False
    print("QRSorting Exit")


rect = None
size = (640, 480)  # 设置采集图片(流)大小
rotation_angle = 0
unreachable = False  # 判断是否能够抓取
reachtime = 0  # 抵达指定位置的时间
catchtime = 0  # 抓取的时间
text='null'
world_X, world_Y = 0, 0

# 控制机械臂移动


def move():
    global rect
    global _stop
    global get_roi
    global move_square
    global __isRunning
    global unreachable
    global detect_color
    global __target_color
    global count
    global text
    global start_pick_up
    global start_pick_down
    global pick_up
    global rotation_angle
    global world_X, world_Y
    global z_r, z_g, z_b, z

    while True:
        # print("detect_color 1=%s" % detect_color)
        if __isRunning:
            # print("detect_color=%s" % detect_color)
            # print(start_pick_up)
            # 检测到特定二维码内容时才会抓取
            # if text == '000000004':
            #     detect_color = ('blue')
            #     # start_pick_up = True
            # elif text == '100000020':
            #     detect_color = ('red')
            #     # start_pick_up = True
            # elif text == '000000003':
            #     detect_color = ('green')
            #     # start_pick_up = True
            # else:
            #     detect_color = 'None'
            get_it=False
            while not get_it:
                if detect_color != 'None' and start_pick_up:  # 如果检测到方块没有移动一段时间后，开始夹取
                    set_rgb(detect_color)
                    # setBuzzer(0.1)
                    # print("begin catch……")
                    reachtime = 0.0
                    # 高度累加
                    z = coordinate[detect_color][2]
                    # z_r += dz
                    # if z == 2 * dz + coordinate['red'][2]:
                    #     z_r = coordinate['red'][2]
                    # if z == coordinate['red'][2]:
                    #     move_square = True
                    #     time.sleep(3)
                    #     move_square = False
                    print("move to world_X=%d"%(world_X) +"and world_Y=%d"%(world_Y))
                    result = AK.setPitchRangeMoving(
                        (world_X, world_Y, 7), -90, -90, 0)  # 移到目标位置，高度5cm
                    if result == False:
                        unreachable = True
                    else:
                        unreachable = False
                        reachtime += result[2]/1000
                        time.sleep(result[2]/1000)
                        print("reachtime=%d"%(reachtime))

                        if not __isRunning:
                            continue
                        # 计算夹持器需要旋转的角度
                        servo2_angle = getAngle(world_X, world_Y, rotation_angle)
                        Board.setBusServoPulse(1, servo1 - 280, 500)  # 爪子张开
                        Board.setBusServoPulse(2, servo2_angle, 500)  # 旋转爪子
                        time.sleep(0.5)

                        if not __isRunning:
                            continue
                        AK.setPitchRangeMoving(
                            (world_X, world_Y, 1.5), -90, -90, 0, 1000)  # 降低高度到2cm
                        time.sleep(1.5)

                        if not __isRunning:
                            continue
                        Board.setBusServoPulse(1, servo1, 500)  # 夹持器闭合
                        time.sleep(0.8)

                        if not __isRunning:
                            continue
                        Board.setBusServoPulse(2, 500, 500)
                        AK.setPitchRangeMoving(
                            (world_X, world_Y, 12), -90, -90, 0, 1000)  # 机械臂抬起
                        time.sleep(1)
                        servo1_now=Board.getBusServoPulse(1)
                        print("servo1_now=%d"%servo1_now)
                        
                        #预运动到码垛区上方
                        AK.setPitchRangeMoving(
                            (0, 10, 12), -90, -90, 0, 1000)  # 机械臂抬起
                        time.sleep(1)
                        #未夹取成功
                        if servo1_now<350:
                            get_it=True
                        else: 
                            print("don't get it")
                            continue
                        pick_up=True
                        start_pick_up=False
                        print("机械臂抬起")
            put_it=False
            while not put_it:
                if detect_color!='None'and start_pick_down:
                    print("机械臂开始放下 detect_color=%s"%detect_color)
                    pick_up=False
                    start_pick_up=False
                    if not __isRunning:
                        continue
                    result=AK.setPitchRangeMoving(
                        (coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0)
                    print(result)
                    time.sleep(result[2]/1000)

                    # if not __isRunning:
                    #     continue
                    # servo2_angle = getAngle(
                    #     coordinate[detect_color][0], coordinate[detect_color][1], -90)
                    # Board.setBusServoPulse(2, servo2_angle, 500)
                    # time.sleep(0.5)

                    if not __isRunning:
                        continue
                    result=AK.setPitchRangeMoving(
                        (coordinate[detect_color][0], coordinate[detect_color][1], z + count[detect_color]*3), -90, -90, 0)
                    print(result)
                    if not result:
                        continue
                    time.sleep(result[2]/1000)

                    # if not __isRunning:
                    #     continue
                    # AK.setPitchRangeMoving(
                    #     (coordinate[detect_color][0], coordinate[detect_color][1], z), -90, -90, 0, 1000)
                    # AK.setPitchRangeMoving((coordinate[detect_color]), -90, -90, 0, 1000)
                    # time.sleep(0.8)

                    if not __isRunning:
                        continue
                    Board.setBusServoPulse(1, servo1 - 200, 500)  # 爪子张开  ，放下物体
                    put_it=True
                    n=count[detect_color]
                    count[detect_color]=n+1
                    print("num %s"%(detect_color)+"=%d"%(n+1))
                    time.sleep(1)

                    if not __isRunning:
                        continue
                    AK.setPitchRangeMoving(
                        (coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0, 800)
                    time.sleep(0.8)
                    detect_color = 'None'
                    __target_color='None'
                    get_roi = False
                    start_pick_up = False
                    text='null'
                    set_rgb(detect_color)
                    initMove()  # 回到初始位置
                    time.sleep(1.5)
                else:
                    if _stop:
                        _stop = False
                        Board.setBusServoPulse(1, servo1 - 70, 300)
                        time.sleep(0.5)
                        Board.setBusServoPulse(2, 500, 500)
                        AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)
                        time.sleep(1.5)
                        # initMove()
                        time.sleep(1.5)
                    time.sleep(0.01)


# 运行子线程
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

# 识别处理图片
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
    # 在二值图像中寻找轮廓, 然后根据区域大小对该轮廓进行排序，保留最大的一个轮廓
    cnts = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0]

    if len(cnts) == 0:
        return None, None, None

    c = sorted(cnts, key=cv2.contourArea, reverse=True)[0]
    # 计算最大的轮廓的最小外接矩形
    rect = cv2.minAreaRect(c)
    box = cv2.boxPoints(rect)
    box = np.int0(box)

    # print(box)

    # 以下是为了将盒子中的图像遮住防止误识别
    # 计算二维码的轮廓的最大最小的坐标值
    x_max = x_min = y_max = y_min = 0
#     print(rect)
    x_min = box[0][0]
    y_min = box[0][1]
    for i in range(4):
        for j in range(2):
            if j == 0:
                if box[i][j] > x_max:
                    x_max = box[i][j]
                elif box[i][j] < x_min:
                    x_min = box[i][j]
            if j == 1:
                if box[i][j] > y_max:
                    y_max = box[i][j]
                elif box[i][j] < y_min:
                    y_min = box[i][j]
    black_box = [[] for i in range(4)]
    # 把遮盖位置左右边界扩大根据盒子和二维码张贴位置自行调整
    # x_min -= 20
    # x_max += 40
    # 防止操作越界
    # if x_min < 0:
    #     x_min = 0
    # if x_max > 640:
    #     x_max = 640
    # 计算二维码的轮廓的最大最小的坐标值
    # black_box[0] = (x_min, y_max)
    # black_box[1] = (x_min, 0)
    # black_box[2] = (x_max, 0)
    # black_box[3] = (x_max, y_max)
    # 提取二维码后的盒子的坐标
    black_box = np.int0(black_box)
    # print(black_box)
    return box, rect, black_box


def angle(a, R=10):
    x = 0.0
    y = 0.0
    if a >= 0 and a <= 180:
        if a == 0:
            x = R
            y = 0.0
            return x, y
        elif a == 90:
            x = 0
            y = R
            return x, y
        elif a == 180:
            x = -R
            y = 0.0
            return x, y
        else:
            y = sin(pi/180*a)*R
            x = y/tan(pi/180*a)
            return x, y
    else:
        pass


def decodeDisplay(image):
    barcodes = pyzbar.decode(image)
    data = []
    box=None
    rect=None
    if not barcodes:
            print('No barcode found.')
            time.sleep(1)
            return image,box,rect, data
    # 记录最大面积的二维码
    max_area = 0
    max_barcode = None
    # 遍历所有二维码
    for barcode in barcodes:
        # 计算二维码轮廓面积
        area = barcode.rect.width * barcode.rect.height
        # 如果当前二维码面积更大，则记录下该二维码
        if area > max_area:
            max_area = area
            max_barcode = barcode
    print("max_area=%d"%max_area)
    # 如果找到了最大面积的二维码，则输出二维码信息和边框位置
    if max_barcode is not None:
        # 输出二维码信息
        print(max_barcode.data.decode('utf-8'))
        # 找到二维码的最小边框位置
        rect = cv2.minAreaRect(np.array(max_barcode.polygon, np.int32))
        box = cv2.boxPoints(rect)
        box = np.int0(box)
    (x, y, w, h) = max_barcode.rect
    print("x=%d"%(x)+"y=%d"%(y))
    barcodeData = max_barcode.data.decode("utf-8")
    data.append([x, y, w, h, barcodeData])
    return image,box,rect, data


# def find_bar_code(box, rect, frame, data):
#重新从图片检测绝对地址
def get_worldposition():
    global rect
    global roi
    global rotation_angle
    global __target_color
    global get_roi

    if rect is not None:
                # print(rect)
                if box is not None:
                    # 获取方块的现实世界坐标
                    roi = getROI(box)  # 获取roi区域
                    get_roi = True
                    img_centerx, img_centery = getCenter(
                        rect, roi, size, square_length)  # 获取木块中心坐标
                    rotation_angle=rect[2]
                    world_X, world_Y = convertCoordinate(
                        img_centerx, img_centery, size)  # 转换为现实世界坐标
                    print("world_X= %d" % (world_X)+" world_Y=%d" % (world_Y))
                    # 框出二维码或二维码部分
                    cv2.drawContours(frame, [box], -1, (0, 255, 0), 2)
                    cv2.imshow('img', img)

# target_color,暂时用颜色代替地址
def get_text():
    global __target_color
    global text
    global start_pick_up
    global start_pick_down
    __target_color=__target_color
    print('func get_text() started')
    return (True,(text))
#心跳检测，用以返回当前机械臂状态
# 0 未识别到数据  1抓取阶段
# 2 放置阶段  3抓取悬空阶段
def Heartbeat(alive):
    global start_pick_up
    global start_pick_down
    global pick_up
    global text
    if text=='null':
        return (True,(0))
    if alive:
        start_pick_up=True
        return (True,(1))
    if pick_up:
        return (True,(3))
    if start_pick_up:
        return (True,(1))
    if start_pick_down:
        return (True,(2))



# def setTargetColor(target_color):
#     global __target_color
#     global text
#     global start_pick_up
#     global start_pick_down
#     print('func setTargetColor() started')
#     if target_color=='None':
#         return (True,(text))
#     else:
#         # print("COLOR", target_color)
#         __target_color = target_color
#         if text!='null':
#             start_pick_down=True
#         else:
#             start_pick_down=False
#         return (True, (text))

def setTargetColor(target_color):
    global __target_color
    global text
    global start_pick_up
    global start_pick_down
    print('func setTargetColor() started')
    if target_color=='None':
        return (True,(text))
    else:
        # print("COLOR", target_color)
        __target_color = target_color
        if text!='null':
            start_pick_down=True
        else:
            start_pick_down=False
        return (True, (text))

""" def QRcode_sort():
    print('func QRcode_sort() started')
    global detect_color
    global rotation_angle
    global start_pick_up
    global __target_color
    global get_roi

    init()
    start()
    my_camera = Camera.Camera()
    my_camera.camera_open()
    while True:
        frame = my_camera.frame
        if frame is not None:
            img = frame.copy()
            # 检测图像中的二维码内容,仅限一个
            img, data = decodeDisplay(img)
            my_camera.camera_close()
            cv2.destroyAllWindows()
            if len(data)!=0:
                text = data[0][4]
                # start_pick_up = True
                print('return text')
                return (True,(text))
            else:
                __target_color = 'None'
                print('return None')
                return (True,('None'))                    
                    # if len(data) != 0:
                        # 在frame上显示识别内容
                        # text = data[0][4]
                        # cv2.putText(frame, text, (data[0][0], data[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX,.5, (0, 0, 125), 2)
                        # xx, yy = convertCoordinate(
                        #     data[0][0], data[0][1], size)
                        # print(xx, yy)
                        # 检测到特定二维码内容时才会抓取
                        # if data[0][4] == '000000004':
                        #     detect_color = ('blue')
                        #     start_pick_up = True
                        #     # coordinate['blue'] = (xx+2, yy+5, 12)
                        # elif data[0][4] == '100000020':
                        #     detect_color = ('red')
                        #     start_pick_up = True
                        #     # coordinate['red'] = (xx+2, yy+5, 12)
                        # elif data[0][4] == '000000003':
                        #     detect_color = ('green')
                        #     start_pick_up = True
                        #     # coordinate['green'] = (xx+2, yy+5, 12)
                        # else:
                        #     detect_color = 'None'
                        # return text
                    # else:
                    #     __target_color = 'None'
                    #     return 'None'

            # img = run(img)
            # cv2.imshow('frame', frame)
            # key = cv2.waitKey(1)
            # if key == 27:
            #     break
            # else:
            #     my_camera.camera_close()
            #     cv2.destroyAllWindows()
            #     # 返回编号
            #     # 如果采用预抓取则不需要返回方块位置
            #     return 'None' """
def QRcode_sort_debug():
    print('func QRcode_sort() started')
    global detect_color
    global rotation_angle
    global start_pick_up
    global start_pick_down
    global __target_color
    global get_roi
    global world_X, world_Y

    init()
    start()
    my_camera = Camera.Camera()
    my_camera.camera_open()
    while True:
        frame = my_camera.frame
        if frame is not None:
            img = frame.copy()
            # 检测图像中的二维码内容,仅限一个
            img,box, rect,data = decodeDisplay(img)
            # 计算出二维码的位置和盒子位置
            # box, rect, black_box = detect(img)
            
            # my_camera.camera_close()
            # cv2.destroyAllWindows()
            # print(rect)
            if rect is not None:
                if box is not None:
                # 获取方块的现实世界坐标
                    roi = getROI(box)  # 获取roi区域
                    get_roi = True
                    img_centerx, img_centery = getCenter(
                                rect, roi, size, square_length)  # 获取木块中心坐标
                    rotation_angle=rect[2]
                    world_X, world_Y = convertCoordinate(
                                img_centerx, img_centery, size)  # 转换为现实世界坐标
                    print("world_X= %d" % (world_X)+" world_Y=%d" % (world_Y))
                    # 框出二维码或二维码部分
                    # cv2.drawContours(img, [box], -1, (0, 255, 0), 2)
                    cv2.imshow('img', img)
                    if len(data)==0:
                        # text = data[0][4]
                        # start_pick_up = True
                        print('return text')
                        # return (True,(text))
                    else:
                        __target_color = 'None'
                        # print('return None')
                        # return (True,('None'))                    
                        if len(data) != 0:
                            # 在frame上显示识别内容
                            text = data[0][4]
                            cv2.putText(frame, text, (data[0][0], data[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX,.5, (0, 0, 125), 2)
                            # xx, yy = convertCoordinate(
                            #     data[0][0], data[0][1], size)
                            # print(xx, yy)
                            # 检测到特定二维码内容时才会抓取
                            if data[0][4] == '000000004' or data[0][4]=='000000019':
                                detect_color = 'blue'
                                start_pick_up = True
                                start_pick_down=True
                                # coordinate['blue'] = (xx+2, yy+5, 12)
                            elif data[0][4] == '100000020' or data[0][4]=='000000009':
                                detect_color = 'red'
                                start_pick_up = True
                                start_pick_down=True
                                # coordinate['red'] = (xx+2, yy+5, 12)
                            elif data[0][4] == '000000003'or data[0][4]=='000000005':
                                detect_color = 'green'
                                start_pick_up = True
                                start_pick_down=True
                                # coordinate['green'] = (xx+2, yy+5, 12)
                            else:
                                detect_color = 'None'
                            # return text
                        else:
                            __target_color = 'None'
                            # return 'None'

            # img = run(img)
            cv2.imshow('frame', frame)
            frame=None
            key = cv2.waitKey(1)
            if key == 27:
                break
            else:
                if not __isRunning:
                    my_camera.camera_close()
                    cv2.destroyAllWindows()
                    return
                # 返回编号
                # 如果采用预抓取则不需要返回方块位置
                # return 'None'



    

def run(img):
    global rect
    global _stop
    global get_roi
    global move_square
    global __isRunning
    global unreachable
    global detect_color
    global __target_color
    global count
    global text
    global start_pick_up
    global rotation_angle
    global world_X, world_Y
    global z_r, z_g, z_b, z
    print('func run() started')
    # 检测图像中的二维码内容,仅限一个
    img,box, rect, data = decodeDisplay(img)
    # 计算出二维码的位置和盒子位置
    # box, rect, black_box = detect(img)

    if rect is not None:
    # print(rect)
        if box is not None:
        # 获取方块的现实世界坐标
            roi = getROI(box)  # 获取roi区域
            get_roi = True
            img_centerx, img_centery = getCenter(
                        rect, roi, size, square_length)  # 获取木块中心坐标
            rotation_angle=rect[2]
            world_X, world_Y = convertCoordinate(
                        img_centerx, img_centery, size)  # 转换为现实世界坐标
            # print("world_X= %d" % (world_X)+" world_Y=%d" % (world_Y))
            # 框出二维码或二维码部分
            # cv2.drawContours(img, [box], -1, (0, 255, 0), 2)
            # cv2.imshow('img', img)
            if len(data) != 0 and text=='null':
            # 在frame上显示识别内容
                text = data[0][4]
                cv2.putText(img, text, (data[0][0], data[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                    .5, (0, 0, 125), 2)
                # xx, yy = convertCoordinate(
                #     data[0][0], data[0][1], size)
                # print(xx, yy)
                if text!='null':
                    start_pick_up=True
        else:
            __target_color = 'None'
        # print('func run() finished')
        return (True,("run "+text))
        

if __name__ == '__main__':
    print('func main() started')
    QRcode_sort_debug()
    # init()
    # start()
    # my_camera = Camera.Camera()
    # my_camera.camera_open()
    # while True:
    #     frame = my_camera.frame
    #     if frame is not None:
    #         img = frame.copy()
    #         # 检测图像中的二维码内容,仅限一个
    #         img, data = decodeDisplay(img)
    #         # 计算出二维码的位置和盒子位置
    #         box, rect, black_box = detect(img)

    #         if rect is not None:
    #             # print(rect)
    #             if box is not None:
    #                 # 获取方块的现实世界坐标
    #                 roi = getROI(box)  # 获取roi区域
    #                 get_roi = True

    #                 img_centerx, img_centery = getCenter(
    #                     rect, roi, size, square_length)  # 获取木块中心坐标
    #                 rotation_angle=rect[2]
    #                 world_X, world_Y = convertCoordinate(
    #                     img_centerx, img_centery, size)  # 转换为现实世界坐标
    #                 print("world_X= %d" % (world_X)+" world_Y=%d" % (world_Y))
    #                 # 框出二维码或二维码部分
    #                 cv2.drawContours(frame, [box], -1, (0, 255, 0), 2)
    #                 cv2.imshow('img', img)
    #                 if len(data) != 0:
    #                     # 在frame上显示识别内容
    #                     text = data[0][4]
    #                     cv2.putText(frame, text, (data[0][0], data[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX,
    #                                 .5, (0, 0, 125), 2)
    #                     xx, yy = convertCoordinate(
    #                         data[0][0], data[0][1], size)
    #                     # print(xx, yy)
    #                     # 检测到特定二维码内容时才会抓取
    #                     if data[0][4] == '000000004':
    #                         detect_color = ('blue')
    #                         start_pick_up = True
    #                         # coordinate['blue'] = (xx+2, yy+5, 12)
    #                     elif data[0][4] == '100000020':
    #                         detect_color = ('red')
    #                         start_pick_up = True
    #                         # coordinate['red'] = (xx+2, yy+5, 12)
    #                     elif data[0][4] == '000000003':
    #                         detect_color = ('green')
    #                         start_pick_up = True
    #                         # coordinate['green'] = (xx+2, yy+5, 12)
    #                     else:
    #                         detect_color = ('None')
    #                 else:
    #                     __target_color = ('None')

    #         # img = run(img)
    #         cv2.imshow('frame', frame)
    #         key = cv2.waitKey(1)
    #         if key == 27:
    #             break
    # my_camera.camera_close()
    # cv2.destroyAllWindows()