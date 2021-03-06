import numpy as np
import cv2
import sys
import os
import time

#import matplotlib offscreen
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from PyQt5.QtCore import QThread, pyqtSignal
sys.path.append('../Common')
from Constants import *
from MessageSocket import *

# Receive and process header and images
# N on concluding experiments
#   linearize = true : Revert gamma corection of Jpeg before merging
#   crf = True : Precalculate the camera response forDebevec merge
# It seems that the Debevec merge without the camera response (ie a linear response) gives the best result
# it seems also that Durand's Tonemap gives the best result
# Note: sharpness is useful for focusing
# Focus your lens to have the maximum sharpness


class ImageThread (QThread):
    threadRunning = False
    imageSignal = pyqtSignal([object, ])   # Signal to the GUI display image
    headerSignal = pyqtSignal([object, ])  # Signal to the GUI display header
    plotSignal = pyqtSignal([object, ])  # Signal to the GUI display analyze
    histogramSignal = pyqtSignal([object, ])  # Signal to the GUI: histogram
    statusSignal = pyqtSignal()  # Signal to the GUI to display image thread info
    merge = MERGE_NONE
    brackets = 1
    sharpness = False
    # saveToFile = False
    histos = False
    images = []
    shutters = []
    startframe = 1
    currentframe = 1
    captureStatusInfo = ""

    def __init__(self, ip_pi):
        QThread.__init__(self)
        self.threadID = 1
        self.name = "ImgThread"
        self.window = None
        self.saveOn = False
        self.startframe = 1
        self.mergeMertens = cv2.createMergeMertens(1, 1, 1)
#         self.mergeMertens = cv2.createMergeMertens()
#         print("Contrast:",self.mergeMertens.getContrastWeight())
#         print("Saturation:",self.mergeMertens.getSaturationWeight())
#         print("Exposure:",self.mergeMertens.getExposureWeight())
        self.mergeDebevec = cv2.createMergeDebevec()
        self.calibrateDebevec = cv2.createCalibrateDebevec()
        self.toneMap = cv2.createTonemapReinhard()
#        self.claheProc = cv2.createCLAHE(clipLimit=1, tileGridSize=(8,8))
#        self.simpleWB = cv2.xphoto.createSimpleWB()
#        self.simpleWB = cv2.xphoto.createGrayworldWB()
#        self.wb= False
#         self.equalize = False
#         self.clahe = False
#        self.clipLimit = 1.
        self.invgamma = np.empty((1, 256), np.uint8)
        for i in range(256):
            self.invgamma[0, i] = np.clip(pow(i / 255.0, 0.45) * 255.0, 0, 255)
        self.gamma = np.empty((1, 256), np.uint8)
        for i in range(256):
            self.gamma[0, i] = np.clip(pow(i / 255.0, 2.2) * 255.0, 0, 255)
        self.reduceFactor = 1
        self.ip_pi = ip_pi
        self.hflip = False
        self.vflip = False
        self.table = None
        self.doCalibrate = False
        try:
            npz = np.load("calibrate.npz")
            self.table = npz['table']
        except (Exception, BaseException):
            pass
        self.threadRunning = True

#     def simplest_cb(self, img, percent):
#         out_channels = []
#         channels = cv2.split(img)
#         totalstop = channels[0].shape[0] * channels[0].shape[1] * percent / 200.0
#         for channel in channels:
#             bc = cv2.calcHist([channel], [0], None, [256], (0,256), accumulate=False)
#             lv = np.searchsorted(np.cumsum(bc), totalstop)
#             hv = 255-np.searchsorted(np.cumsum(bc[::-1]), totalstop)
#             lut = np.array([0 if i < lv else (255 if i > hv else round(float(i-lv)/float(hv-lv)*255)) for i in np.arange(0, 256)], dtype="uint8")
#             out_channels.append(cv2.LUT(channel, lut))
#         return cv2.merge(out_channels)

    def calcHistogram(self, image):
        histos = []
        for i in range(3):
            histo = cv2.calcHist([image], [i], None, [256], [0, 256])
            histos.append(histo)
        self.displayHistogramOverImage(histos, image)
        
    def displayHistogramOverImage(self, histos, image):
        # PSI: pyplot is not threadsafe -> moving plot code to main
        # figure = plt.figure()
        # axe = figure.add_subplot(111)
        # colors = ('b', 'g', 'r')
        # for i, col in enumerate(colors):
        #     axe.plot(histos[i], color=col)
        # axe.set_xlim([0, 256])
        # axe.get_yaxis().set_visible(False)
        # figure.tight_layout()
        # figure.canvas.draw()
        # canvasWidth, canvasHeight = figure.canvas.get_width_height()
        # buf = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8).reshape(canvasHeight, canvasWidth, 3)
        # plt.close()
        # self.plotSignal.emit(buf)  # «display plot in the GUI
        self.histogramSignal.emit(histos)
#         ww = int(image.shape[0]/4)
#         hh = int(h*ww/w)
#         resized = cv2.resize(buf, dsize=(ww,hh), interpolation=cv2.INTER_CUBIC)
#         image[:hh,:ww] = resized


    def processImage(self, header, jpeg):
        bracket = header['bracket']
        count = header['count']
        jpeg = np.frombuffer(jpeg, np.uint8, count=len(jpeg))
        image = cv2.imdecode(jpeg, 1)   # Jpeg decoded
        #update status
        self.captureStatusInfo = "processing image"
        self.statusSignal.emit()

        isJpeg = True
        if self.merge != MERGE_NONE and bracket != 0:  # Merge We receive bracket 3 2 1
            # image = cv2.LUT(image, self.gamma)
            self.images.append(image)
            self.shutters.append(header['shutter'])
            if bracket != 1:
                return
            else:
                if self.merge == MERGE_MERTENS:
                    image = self.mergeMertens.process(self.images)
                    image = cv2.normalize(image, None, 0., 1., cv2.NORM_MINMAX)
                else:
                    times = np.asarray(self.shutters, dtype=np.float32)/1000000.
#                    responseDebevec = self.calibrateDebevec.process(self.images, times)
#                    image = self.mergeDebevec.process(self.images, times, responseDebevec)
                    image = self.mergeDebevec.process(self.images, times)
                    image = self.toneMap.process(image)
                if self.doCalibrate:
                    image = image * self.table
                image = np.clip(image*255, 0, 255).astype('uint8')
#                image = cv2.LUT(image, self.invgamma)

#                 if self.equalize :
#                     H, S, V = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))
#                     low, high = np.percentile(V, (1, 99))
#                     eq_V = np.interp(V, (low,high), (V.min(), V.max())).astype(np.uint8)
#                     image = cv2.cvtColor(cv2.merge([H, S, eq_V]), cv2.COLOR_HSV2BGR)
#                 if self.clahe :
#                     H, S, V = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))
#                     self.claheProc.setClipLimit(self.clipLimit)
#                     eq_V = self.claheProc.apply(V)
#                     image = cv2.cvtColor(cv2.merge([H, S, eq_V]), cv2.COLOR_HSV2BGR)
#                 if self.wb :
#                     image = self.simpleWB.balanceWhite(image)
#                     image = self.simplest_cb(image, 1)
                isJpeg = False
                self.images.clear()
                self.shutters.clear()
        elif self.doCalibrate:
            image = image * self.table
            image = np.clip(image, 0, 255).astype('uint8')
            image = image.astype(np.uint8)
            isJpeg = False

        if self.saveOn:
            self.currentframe = count + (self.startframe - 1)
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
            if isJpeg:
                if bracket != 0:
                    file = open(self.directory + "/image_%#05d_%#02d.jpg" % (self.currentframe, bracket), 'wb')
                else:
                    file = open(self.directory + "/image_%#05d.jpg" % self.currentframe, 'wb')
                file.write(jpeg)
                file.close()
            else:
                cv2.imwrite(self.directory + "/image_%#05d.jpg" % self.currentframe, image)
                
        if isJpeg and bracket == 0 and self.sharpness:
            sharpness = cv2.Laplacian(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
            cv2.putText(image, str(sharpness), (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 2)
        
        if self.histos:
            self.calcHistogram(image)
        if self.reduceFactor != 1:
            newShape = (int(image.shape[1]/self.reduceFactor), int(image.shape[0]/self.reduceFactor))
            image = cv2.resize(image, dsize=newShape, interpolation=cv2.INTER_CUBIC)            
        self.imageSignal.emit(image)  # «display image in the GUI
#         print(np.min(image, axis=(0,1)))
#         print(np.max(image, axis=(0,1)))
#         print(np.mean(image, axis=(0,1)))
#         cv2.imshow("PiCamera", image)
#         cv2.waitKey(1)
        #update status
        self.captureStatusInfo = "ready"
        self.statusSignal.emit()
        time.sleep(0)  #yield other threads

        # def lensAnalyze(self, header) :
    def lensAnalyze(self):
        image = self.imageSock.receiveArray()  # bgr
        if self.doCalibrate:
            image = image * self.table
            image = image.astype(np.uint8)
        x = image.shape[0]/image.shape[1]
        valuesDiagonal = np.empty((image.shape[1], 3))
        for i in range(image.shape[1]):  # 3280
            j = int(i * x)
            valuesDiagonal[i, :] = image[j, i, :]

        colors = ('b', 'g', 'r')
        figure = plt.figure(figsize=(10, 3))
        axe = figure.add_subplot(1, 3, 1)
        axe.title.set_text('Horizontal')
        for i, col in enumerate(colors):
            axe.plot(image[image.shape[0]//2, :, i], color=col)  # Horizontal
        axe = figure.add_subplot(1, 3, 2)
        axe.title.set_text('Vertical')
        for i, col in enumerate(colors):
            axe.plot(image[:, image.shape[1]//2, i], color=col)  # Vertical
        axe = figure.add_subplot(1, 3, 3)
        axe.title.set_text('Diagonal')
        for i, col in enumerate(colors):
            axe.plot(valuesDiagonal[:, i], color=col)  # Diagonal
#        figure.subplots_adjust(top=0.85)
        figure.tight_layout()
        figure.canvas.draw()
        plt.close()
        canvasWidth, canvasHeight = figure.canvas.get_width_height()
        image = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8).reshape(canvasHeight, canvasWidth, 3)
        self.plotSignal.emit(image)  # «display plot in the GUI
#        plt.show()

# Normalize each channel toward the Min
    def calibrate(self, header):
        image = self.imageSock.receiveArray()  # bgr
        i = header['num']
        count = header['count']
        if i != 0:
            image = image * self.table
        gains = np.copy(image).astype(np.float)
#        ih, iw, nc = image.shape
#        centre = np.min(image, axis=(0, 1))
        centre = np.mean(image, axis=(0, 1))

#         print(np.min(image, axis=(0, 1)))
#         print(np.max(image, axis=(0, 1)))
#         print(np.mean(image, axis=(0, 1)))
        gains = centre/gains
        if i == 0:    # First one
            self.table = gains
        else:
            self.table = self.table*gains
#         print(np.min(self.table, axis=(0, 1)))
#         print(np.max(self.table, axis=(0, 1)))
#        self.table[self.table>1.] = 1.
        if i == count - 1:
            np.savez('calibrate.npz', table=self.table)
        header = {'type': HEADER_MESSAGE, 'msg': "Local Calibration done"}
        self.headerSignal.emit(header)  # «display header info in GUI if necessary (count,...)
            
    def saveToFile(self, saveFlag, directory, startframe):
        self.saveOn = saveFlag
        self.directory = directory
        self.startframe = startframe

    def run(self):
        print('ImageThread started')
        self.imageSock = None
        try:
            sock = socket.socket()
            sock.connect((self.ip_pi, 8000))
            print('ImageThread connected')
            self.imageSock = MessageSocket(sock)
            while True:
                header = self.imageSock.receiveObject()
                # if header == None :
                if header is None:
                    print('Closed connection')
                    cv2.destroyAllWindows()
                    # if self.imageSock != None:
                    if self.imageSock is not None:
                        self.imageSock.close()
                    break
                typ = header['type']
                if typ == HEADER_STOP:
                    break
                self.headerSignal.emit(header)  # «display header info in GUI if necessary (count,...)
                if typ == HEADER_IMAGE:
                    image = self.imageSock.receiveMsg()
                    self.processImage(header, image)
                elif typ == HEADER_BGR:
                    self.processBgr()
                elif typ == HEADER_CALIBRATE:
                    self.calibrate(header)
                elif typ == HEADER_ANALYZE:
                    # self.lensAnalyze(header)
                    self.lensAnalyze()
#                if  typ == HEADER_HDR :
#                    image = self.imageSock.receiveMsg()
#                    self.processHdrImage(header, image)
                
        finally:
            print('ImageThread terminated')
            cv2.destroyAllWindows()
            # if self.imageSock != None:
            if self.imageSock is not None:
                self.imageSock.shutdown()
                self.imageSock.close()

# Experimental Receive a set of exposures not used
#     def processHdrImage(self, header, jpeg):
#         jpeg = np.frombuffer(jpeg, np.uint8,count = len(jpeg))
#         file = open(self.directory + "/ldr_%#05d.jpg" % (header['shutter']) ,'wb')
#         file.write(jpeg)
#         file.close()
#         image = cv2.imdecode(jpeg, 1)   #Jpeg decode
#         cv2.imshow("PiCamera", image)
#         cv2.waitKey(1)
