#encoding=utf-8
# __author__ = 'Meng xian bang'
# 11/07/2025

import nuke
import os
import subprocess
import platform
import getpass
import sys


operatingSystem = platform.system()




#旧项目使用nuke12打开，根目录会指认老服务器盘符
#if nuke.NUKE_VERSION_STRING == '11.3v6':
if nuke.NUKE_VERSION_MAJOR < 12:
    manager_dir = "Z:"
else:
    manager_dir = "W:"
projectmanager_dir = manager_dir




#插件全局权限设置
current_user = getpass.getuser()
if current_user in ['1','2','00','00','00','00']:
   user_name = "false"
else:
   user_name = "true"
 



#素材库需要读取的ffmpeg的路径
ffmpegPath1 = '//SERVER/tools/shiningvfx_nuke15/ffmpeg/bin/ffmpeg.exe'

#分享插件captured的配置文件的路径
capture_txt1 = "//SERVER/tools/shiningvfx_nuke15/path_Settings/"

#分享插件captured的节点存放路径的默认设置
cN1 = 'W:\Tools\share\capturedNodes'

#分享插件captured的图片存放路径的默认设置
cI1 = 'W:\Tools\share\capturedImages'

#素材库插件的设置文件路径
Eset1 = '//SERVER/tools/shiningvfx_nuke15/path_Settings/Ulaavi/preference/settings.json'

#rv的安装路径
rv1 = 'C:/Program Files/Shotgun/RV-2021.0.2/bin/rv.exe'

#python读取的PyMySQL外挂插件的路径
sql1 = r"\\SERVER\tools\shiningvfx_nuke15\path_Settings\PyMySQL"


#陈康管理软件相关设置
#服务器IP地址
my_host = '192.168.199.42'
#登陆账号
my_user = 'root'
#登陆密码
my_password = 'BBfe9~.+'
#数据表名
my_database = 'server'


#set plugins dir
ffmpegPath_dir = ffmpegPath1.replace("\\", "/")
capture_txt_Dir = capture_txt1.replace("\\", "/")
capturedI = cI1.replace("\\", "/")
capturedN = cN1.replace("\\", "/")
Element_Library_set = Eset1.replace("\\", "/")
rv_file = rv1.replace("\\", "/")
my_pm_sql = sql1.replace("\\", "/")



