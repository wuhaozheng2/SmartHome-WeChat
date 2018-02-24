#!/bin/sh

STREAMER=mjpg_streamer
DEVICE=/dev/video0
RESOLUTION=320x240
FRAMERATE=10
MJPG_WEB_ROOT=/home/pi/test/www/
HTTP_PORT=8001
PLUGINPATH=/usr/lib
echo “正在加载摄像头驱动”
$STREAMER -i "$PLUGINPATH/input_uvc.so -n -d $DEVICE -r $RESOLUTION -f $FRAMERATE -y YUYV" -o "$PLUGINPATH/output_http.so -w $MJPG_WEB_ROOT -p $HTTP_PORT " &

echo “正在启动主程序”

sudo python main.py 80
