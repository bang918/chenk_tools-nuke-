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




manager_dir = "W:"
projectmanager_dir = manager_dir




#插件全局权限设置
current_user = getpass.getuser()
if current_user in ['1','2','00','00','00','00']:
   user_name = "false"
else:
   user_name = "true"
 

#python读取的PyMySQL外挂插件的路径
sql1 = r"\\SERVER\tools\shiningvfx_nuke15\path_Settings\PyMySQL"


#陈康管理软件相关设置
#服务器IP地址
my_host = '192.168.199.1'
#登陆账号
my_user = 'root'
#登陆密码
my_password = '0123'
#数据表名
my_database = 'server'


#set plugins dir
my_pm_sql = sql1.replace("\\", "/")



