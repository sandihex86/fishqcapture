
import cv2
import depthai as dai
import time
import logging
import logging.handlers
import argparse
from pathlib import Path

parser = argparse.ArgumentParser("Capture data for FishQ Pusriskan")
parser.add_argument('FPS', type=int, help="Capture video in this FPS")
parser.add_argument('namaFolder',type=str, help="Nama folder untuk menyimpan data",const='/media/fishqi/FISHQ_STORE/RECORDING/')
args = parser.parse_args()



''' Script untuk meng-capture data sebelum ditraining 
    Script date : 04 Oktober 2021


'''
''' configure the logger '''
logger = logging.getLogger('myCaptureLogger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s -%(name)s -%(message)s')
handler = logging.handlers.RotatingFileHandler('FishqCapture.log', maxBytes=10000, backupCount=5)
handler.setFormatter(formatter)
streamer = logging.StreamHandler()
streamer.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(streamer)

logger.debug(f"capturing in {args.FPS} FPS, data disimpan di /{args.namaFolder}/*")
#set parameter
fps = args.FPS
folderName = args.namaFolder

def create_pipeline():
    ''' create pipeline '''
    pipeline = dai.Pipeline()

    ''' color camera properties '''
    camRgb = pipeline.createColorCamera()
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    camRgb.setFps(fps)
    xoutRgb = pipeline.createXLinkOut()
    xoutRgb.setStreamName("rgb")
    camRgb.video.link(xoutRgb.input)
    videoEnc = pipeline.createVideoEncoder() #create video encoder
    videoEnc.setDefaultProfilePreset(camRgb.getVideoSize(), camRgb.getFps(), dai.VideoEncoderProperties.Profile.MJPEG)
    camRgb.video.link(videoEnc.input)
    xoutJpeg = pipeline.createXLinkOut()
    xoutJpeg.setStreamName("jpeg")
    videoEnc.bitstream.link(xoutJpeg.input)

    ''' mono right camera '''
    monoRight = pipeline.createMonoCamera()
    monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)
    monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)
    monoRight.setFps(fps)
    xoutRight = pipeline.createXLinkOut()
    xoutRight.setStreamName("monoright")
    monoRight.out.link(xoutRight.input)

    ''' mono left camera '''
    monoLeft = pipeline.createMonoCamera()
    monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
    monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)
    monoLeft.setFps(fps)
    xoutLeft = pipeline.createXLinkOut()
    xoutLeft.setStreamName("monoleft")
    monoLeft.out.link(xoutLeft.input)

    return(pipeline)

class Main():
    def __init__(self):
        self.name = 'apps capture'
    def run(self):
        logger.debug('Create pipeline')
        pipeline = create_pipeline()
        with dai.Device(pipeline) as device:
            logger.debug('Start pipeline')
            device.startPipeline()
            qRgb = device.getOutputQueue(name="rgb", maxSize=30, blocking=False)
            qJpeg = device.getOutputQueue(name="jpeg", maxSize=30, blocking=True)
            qRight = device.getOutputQueue(name="monoright", maxSize=4, blocking=False)
            qLeft = device.getOutputQueue(name="monoleft", maxSize=4, blocking=False)

            # Memastikan folder ouput tersedia
            Path(f'{folderName}_color_data').mkdir(parents=True, exist_ok=True)
            Path(f'{folderName}_right_data').mkdir(parents=True, exist_ok=True)
            Path(f'{folderName}_left_data').mkdir(parents=True, exist_ok=True)

            while True:
                inRgb = qRgb.tryGet()  # Non-blocking call, will return a new data that has arrived or None otherwise
                inRight = qRight.tryGet()
                inLeft = qLeft.tryGet()

                if inRgb is not None:
                    cv2.imshow("fishQ:COLOR-CAMERA", inRgb.getCvFrame())

                if inRight is not None:
                    cv2.imshow("fishQ:MONO-KANAN",inRight.getCvFrame())
                    cv2.imwrite(f"{folderName}_right_data/{int(time.time()*10000)}.png",inRight.getCvFrame())

                if inLeft is not None:
                    cv2.imshow("fishQ:MONO-KIRI",inLeft.getCvFrame())
                    cv2.imwrite(f"{folderName}_left_data/{int(time.time()*10000)}.png",inLeft.getCvFrame())

                for encFrame in qJpeg.tryGetAll():
                    with open(f"{folderName}_color_data/{int(time.time() * 10000)}.jpeg", "wb") as f:
                        f.write(bytearray(encFrame.getData()))

                if cv2.waitKey(1) == ord('q'):
                    logger.debug("Application fishq capture is Closed by user")
                    break

''' CREATE APPS RUN '''
logger.debug('creating application Capture FishQ')
apps = Main()
apps.run()

