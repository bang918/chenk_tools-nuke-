# -*- coding: utf-8 -*-
import sys
import time
import nuke
from PySide2 import QtWidgets, QtCore, QtGui
from nukescripts import panels
from pathSettings import *
import os
import re

# 添加PyMySQL路径
sys.path.append(my_pm_sql)

import pymysql


class RenderSettingsWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(RenderSettingsWindow, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setWindowTitle("CMD渲染设置")
        self.setMinimumSize(400, 200)
        self.setStyleSheet(self.parent().NUKE_STYLE)  # 复用Nuke风格
        
        # 获取当前选中的工程文件路径
        self.current_file = self.parent().cmb_file.currentData()
        
        # 存储WRITE节点信息
        self.write_nodes = []
        self.root_frame_range = ""
        
        self.init_ui()
        self.load_render_info()
        
    def init_ui(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # WRITE节点选择
        write_layout = QtWidgets.QHBoxLayout()
        write_label = QtWidgets.QLabel("WRITE节点:")
        write_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        write_label.setFixedWidth(80)
        
        self.cmb_write_nodes = QtWidgets.QComboBox()
        self.cmb_write_nodes.setFixedHeight(28)
        
        write_layout.addWidget(write_label)
        write_layout.addWidget(self.cmb_write_nodes)
        main_layout.addLayout(write_layout)
        
        # 帧范围输入
        frame_layout = QtWidgets.QHBoxLayout()
        frame_label = QtWidgets.QLabel("帧范围:")
        frame_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        frame_label.setFixedWidth(80)
        
        self.txt_frame_range = QtWidgets.QLineEdit()
        self.txt_frame_range.setFixedHeight(28)
        
        frame_layout.addWidget(frame_label)
        frame_layout.addWidget(self.txt_frame_range)
        main_layout.addLayout(frame_layout)
        
        # 按钮布局
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("添加到桌面CMD渲染")
        self.btn_add.clicked.connect(self.on_add_render)
        
        self.btn_cancel = QtWidgets.QPushButton("返回")
        self.btn_cancel.clicked.connect(self.close)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
    
    def load_render_info(self):
        """加载选中工程文件中的WRITE节点和ROOT帧范围（修正嵌套括号问题）"""
        if not self.current_file or not os.path.exists(self.current_file):
            nuke.message("错误：未找到选中的工程文件")
            self.close()
            return
            
        try:
            # 读取.nk文件内容并按行分割
            with open(self.current_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f.readlines()]  # 预处理每行，去除首尾空格
            
            self.write_nodes = []
            in_write_block = False  # 是否处于Write节点块内
            bracket_balance = 0     # 括号平衡计数器，处理嵌套括号
            
            for line in lines:
                # 检测Write节点开始：行内容为"Write {"（允许中间有任意空格）
                if re.fullmatch(r'Write\s+\{', line):
                    in_write_block = True
                    bracket_balance = 1  # 初始包含一个左括号
                    continue
                    
                # 处理Write节点内部内容
                if in_write_block:
                    # 更新括号平衡
                    bracket_balance += line.count('{')
                    bracket_balance -= line.count('}')
                    
                    # 检测name行：行以"name "开头（允许前面有空格）
                    name_match = re.match(r'\s*name\s+', line)
                    if name_match:
                        # 提取name后面的内容
                        name_content = line[name_match.end():].strip()
                        # 处理带引号和不带引号的情况
                        if name_content.startswith('"') and name_content.endswith('"'):
                            node_name = name_content[1:-1]  # 去除引号
                        else:
                            # 不带引号时取第一个空格前的内容
                            node_name = name_content.split()[0] if name_content.split() else ""
                        
                        if node_name:
                            self.write_nodes.append(node_name)
                    
                    # 当括号平衡为0时，说明当前Write节点结束
                    if bracket_balance == 0:
                        in_write_block = False
            
            # 去重并排序
            self.write_nodes = sorted(list(set(self.write_nodes)))
            
            if not self.write_nodes:
                nuke.message("警告：当前工程文件中没有找到WRITE节点")
                self.close()
                return
                
            # 填充WRITE节点下拉框
            for node_name in self.write_nodes:
                self.cmb_write_nodes.addItem(node_name, node_name)
                
            # 解析Root块中的帧范围参数（保持原有逻辑）
            root_pattern = re.compile(r'Root\s*\{([^}]+)\}', re.DOTALL)
            # 重新读取文件内容用于Root解析
            with open(self.current_file, 'r', encoding='utf-8', errors='ignore') as f:
                nk_content = f.read()
            root_match = root_pattern.search(nk_content)
            
            first_frame = 1  # 默认起始帧
            last_frame = 100  # 默认结束帧
            
            if root_match:
                root_content = root_match.group(1)
                # 匹配first_frame
                first_pattern = re.compile(r'first_frame\s+(\d+)', re.DOTALL)
                first_match = first_pattern.search(root_content)
                if first_match:
                    first_frame = int(first_match.group(1))
                
                # 匹配last_frame
                last_pattern = re.compile(r'last_frame\s+(\d+)', re.DOTALL)
                last_match = last_pattern.search(root_content)
                if last_match:
                    last_frame = int(last_match.group(1))
            
            # 设置帧范围
            self.root_frame_range = f"{first_frame}-{last_frame}"
            self.txt_frame_range.setText(self.root_frame_range)
            
        except Exception as e:
            nuke.message(f"错误：加载工程文件信息失败: {str(e)}")
            self.close()
    
    def on_add_render(self):
        """添加到桌面CMD渲染"""
        if not self.current_file:
            nuke.message("错误：未选择工程文件")
            return
            
        selected_write_node = self.cmb_write_nodes.currentData()
        frame_range = self.txt_frame_range.text().strip()
        
        if not selected_write_node:
            nuke.message("错误：请选择WRITE节点")
            return
            
        # 增强帧范围验证
        if "-" not in frame_range:
            nuke.message("错误：请输入有效的帧范围(格式: 开始-结束)")
            return
            
        frame_parts = frame_range.split('-')
        if len(frame_parts) != 2:
            nuke.message("错误：帧范围格式错误(格式: 开始-结束)")
            return
            
        try:
            start_frame = int(frame_parts[0].strip())
            end_frame = int(frame_parts[1].strip())
        except ValueError:
            nuke.message("错误：帧范围必须为整数")
            return
            
        if start_frame > end_frame:
            nuke.message("错误：起始帧不能大于结束帧")
            return
            
        try:
            # 获取Nuke可执行文件路径（带引号处理空格）
            nuke_exe_path = nuke.env['ExecutablePath']
            nuke_path = f'"{nuke_exe_path}"'
            
            # 构建渲染命令（与bat_render.py保持一致）
            render_cmd = f'{nuke_path} -x -X {selected_write_node} -F {frame_range} "{self.current_file}"\n'
            
            # 获取桌面路径（兼容中文系统）
            desktop_path = self.get_desktop_path()
            if not os.path.exists(desktop_path):
                nuke.message(f"错误：未找到桌面路径: {desktop_path}")
                return
            
            # 创建CMD文件名（使用当前日期）
            current_time = time.strftime('%m.%d')
            cmd_filename = os.path.join(desktop_path, f"{current_time}.render.cmd")
            
            # 追加写入CMD文件
            with open(cmd_filename, "a+", encoding="utf-8") as f:
                f.write(render_cmd)
            

            nuke.message(f"成功：已添加CMD渲染命令到\n{os.path.basename(cmd_filename)}\n路径: {desktop_path}")
            self.close()
            
        except Exception as e:
            nuke.message(f"错误：创建CMD渲染文件失败: {str(e)}")
    
    def get_desktop_path(self):
        """获取桌面路径（兼容中文系统和特殊路径）"""
        if sys.platform.startswith('win32'):
            # 优先尝试标准Desktop路径
            desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            # 若不存在，尝试中文"桌面"
            if not os.path.exists(desktop_path):
                desktop_path = os.path.join(os.environ['USERPROFILE'], '桌面')
            return desktop_path
        elif sys.platform.startswith('darwin'):
            return os.path.join(os.environ['HOME'], 'Desktop')
        else:
            return os.path.join(os.environ['HOME'], 'Desktop')


def on_add_cmd_render_clicked(self):
    """显示CMD渲染设置窗口"""
    if not self.cmb_file.currentData():
        nuke.message("错误：请先选择工程文件")
        return
        
    # 显示渲染设置窗口
    render_window = RenderSettingsWindow(self)
    render_window.exec_()



class NukeStyleProjectBrowser(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(NukeStyleProjectBrowser, self).__init__(parent)
        # 合并窗口标志设置，确保始终置顶
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setWindowTitle(u"shiningvfx项目浏览器1.2")
        self.setMinimumSize(420, 280)  # 增加窗口高度以容纳新控件

        # Nuke官方配色方案
        self.NUKE_STYLE = """
            QWidget {
                background-color: #353535;
                color: #b4b4b4;
                font-family: Helvetica;
            }
            QLabel {
                font-size: 12px;
                min-width: 60px;
            }
            QComboBox {
                background: #404040;
                border: 1px solid #2f2f2f;
                padding: 5px;
                min-width: 300px;
                selection-background-color: #1864B6;
            }
            QComboBox QAbstractItemView {
                background: #404040;
                selection-background-color: #1864B6;
            }
            QComboBox::drop-down {
                border-left: 1px solid #2f2f2f;
                width: 20px;
            }
            QGroupBox {
                border: 1px solid #2f2f2f;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 3px;
            }
            QCheckBox {
                font-size: 12px;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #2f2f2f;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """
        self.setStyleSheet(self.NUKE_STYLE)

        # 数据库连接
        self.db_conn = None
        
        # 新增：显示关闭项目的复选框状态
        self.show_closed_projects = False

        # 新增：选择制作者的下拉框
        self.cmb_creator = QtWidgets.QComboBox(self)
        self.cmb_creator.addItem("全部", None)
        self.cmb_creator.currentIndexChanged.connect(self.on_creator_changed)

        # 新增：显示关闭项目的复选框和匹配按钮
        self.chk_show_closed = QtWidgets.QCheckBox("显示关闭项目")
        self.chk_show_closed.stateChanged.connect(self.on_show_closed_changed)
        
        # 新增：匹配按钮
        self.btn_match = QtWidgets.QPushButton("匹配")
        self.btn_match.clicked.connect(self.on_match_clicked)

        self.init_ui()
        self.init_db()
        self.load_creators()
        self.load_projects()

    def init_ui(self):
        """Nuke风格布局"""
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # 新增：将制作者标签和下拉框添加到布局中
        creator_layout = QtWidgets.QHBoxLayout()
        creator_label = QtWidgets.QLabel("制作者:")
        creator_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        creator_label.setFixedWidth(70)
        creator_layout.addWidget(creator_label)
        creator_layout.addWidget(self.cmb_creator)
        main_layout.addLayout(creator_layout)

        # 项目管理组
        project_group = QtWidgets.QGroupBox(u"项目管理器")
        group_layout = QtWidgets.QVBoxLayout()
        group_layout.setContentsMargins(10, 20, 10, 10)
        group_layout.setSpacing(12)

        # 新增：显示关闭项目的复选框和匹配按钮放在同一行
        show_closed_layout = QtWidgets.QHBoxLayout()
        show_closed_layout.addWidget(self.chk_show_closed)
        show_closed_layout.addWidget(self.btn_match)
        group_layout.addLayout(show_closed_layout)

        # 项目选择
        project_row = self._create_label_combo(u"项目:", "项目选择")
        self.cmb_project = project_row[1]
        group_layout.addLayout(project_row[0])

        # 集数选择
        episode_row = self._create_label_combo(u"集数:", "集数选择")
        self.cmb_episode = episode_row[1]
        self.cmb_episode.setEnabled(False)
        group_layout.addLayout(episode_row[0])

        # 镜头选择
        shot_row = self._create_label_combo(u"镜头:", "镜头选择")
        self.cmb_shot = shot_row[1]
        self.cmb_shot.setEnabled(False)
        group_layout.addLayout(shot_row[0])

        # 新增：工程文件选择下拉框
        file_row = self._create_label_combo(u"工程文件:", "工程文件选择")
        self.cmb_file = file_row[1]
        self.cmb_file.setEnabled(False)
        group_layout.addLayout(file_row[0])

        # 制作者信息
        self.lbl_creator = QtWidgets.QLabel("Artist: ---")
        self.lbl_creator.setAlignment(QtCore.Qt.AlignRight)
        self.lbl_creator.setStyleSheet("font-size: 13px; color: #909090;")
        group_layout.addWidget(self.lbl_creator)

        # 显示制作阶段状态、内部审核状态、客户审核状态以及反馈内容
        self.lbl_production_status = QtWidgets.QLabel("制作阶段状态: ---")
        self.lbl_production_status.setStyleSheet("font-size: 13px; color: #909090;")
        group_layout.addWidget(self.lbl_production_status)

        self.lbl_nb_shenhe = QtWidgets.QLabel("内部审核状态: ---")
        self.lbl_nb_shenhe.setStyleSheet("font-size: 13px; color: #909090;")
        group_layout.addWidget(self.lbl_nb_shenhe)

        self.lbl_kh_shenhe = QtWidgets.QLabel("客户审核状态: ---")
        self.lbl_kh_shenhe.setStyleSheet("font-size: 13px; color: #909090;")
        group_layout.addWidget(self.lbl_kh_shenhe)

        self.lbl_review_message = QtWidgets.QLabel("反馈内容: ---")
        self.lbl_review_message.setStyleSheet("font-size: 13px; color: #909090;")
        group_layout.addWidget(self.lbl_review_message)

        project_group.setLayout(group_layout)
        main_layout.addWidget(project_group)

        # 底部按钮布局
        button_layout = QtWidgets.QHBoxLayout()
        test_button_1 = QtWidgets.QPushButton("创建工程文件")
        test_button_1.clicked.connect(self.on_test_button_1_clicked)
        test_button_2 = QtWidgets.QPushButton("自动创建工程")
        test_button_2.clicked.connect(self.on_test_button_2_clicked)
        button_layout.addWidget(test_button_1)
        button_layout.addWidget(test_button_2)
        main_layout.addLayout(button_layout)

        new_button_layout = QtWidgets.QHBoxLayout()
        # 打开所选工程按钮
        open_btn = QtWidgets.QPushButton("打开所选工程")
        open_btn.clicked.connect(self.on_open_selected_clicked)
        # 添加CMD渲染按钮
        cmd_btn = QtWidgets.QPushButton("添加CMD渲染")
        cmd_btn.clicked.connect(self.on_add_cmd_render_clicked)
        new_button_layout.addWidget(open_btn)
        new_button_layout.addWidget(cmd_btn)
        main_layout.addLayout(new_button_layout)

        self.setLayout(main_layout)

        # 信号连接
        self.cmb_project.currentIndexChanged.connect(self.on_project_changed)
        self.cmb_episode.currentIndexChanged.connect(self.on_episode_changed)
        self.cmb_shot.currentIndexChanged.connect(self.on_shot_changed)
        # 新增：工程文件选择事件
        self.cmb_file.currentIndexChanged.connect(self.on_file_changed)

    def _create_label_combo(self, label_text, placeholder):
        """创建标签+组合框的行布局"""
        row_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(label_text)
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        label.setFixedWidth(70)

        combo = QtWidgets.QComboBox()
        combo.addItem(f"- {placeholder} -", None)
        combo.setFixedHeight(28)

        row_layout.addWidget(label)
        row_layout.addWidget(combo)
        return row_layout, combo

    def init_db(self):
        try:
            self.db_conn = pymysql.connect(
                host=my_host,
                user=my_user,
                password=my_password,
                database=my_database,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5
            )
        except Exception as e:
            self._show_error("Database Error", f"Connection failed: {str(e)}")

    def load_creators(self):
        if not self.db_conn:
            return

        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("SELECT name FROM tb_participants")
                creators = cursor.fetchall()

                if not creators:
                    self.cmb_creator.addItem("未分配", "未分配")
                else:
                    for creator in creators:
                        self.cmb_creator.addItem(creator['name'], creator['name'])

        except Exception as e:
            self._show_error("Data Error", f"加载制作者列表失败: {str(e)}")

    def load_projects(self):
        if not self.db_conn:
            return

        creator = self.cmb_creator.currentData()
        try:
            with self.db_conn.cursor() as cursor:
                # 基础SQL查询，增加is_active条件判断
                base_sql = """
                    SELECT id, project_name, project_title, is_active 
                    FROM tb_projects 
                """
                
                # 条件列表和参数
                conditions = []
                params = []
                
                # 根据显示关闭项目的状态添加条件
                if not self.show_closed_projects:
                    conditions.append("is_active = 1")
                
                # 处理制作者条件
                if creator and creator != "未分配" and creator != "全部":
                    # 需要关联查询
                    sql = f"""
                        SELECT p.id, p.project_name, p.project_title, p.is_active 
                        FROM tb_projects p
                        JOIN tb_shotinfo si ON p.id = si.project_id
                        { 'WHERE' if conditions else '' } { ' AND '.join(conditions) }
                        { 'AND' if conditions else 'WHERE' } si.creator LIKE %s
                        GROUP BY p.id
                        ORDER BY p.id DESC
                    """
                    params.append('%' + creator + '%')
                else:
                    # 直接查询项目表
                    if conditions:
                        base_sql += " WHERE " + " AND ".join(conditions)
                    base_sql += " ORDER BY id DESC"
                    sql = base_sql
                
                cursor.execute(sql, params)
                projects = cursor.fetchall()

                self.cmb_project.clear()
                self.cmb_project.addItem("- 项目选择 -", None)

                for proj in projects:
                    # 关闭的项目在名称后添加标记
                    status_mark = " (已关闭)" if proj['is_active'] == 0 else ""
                    text = f"{proj['project_name']} ({proj['project_title']}){status_mark}"
                    self.cmb_project.addItem(text, proj['id'])

        except Exception as e:
            self._show_error("Data Error", f"加载项目失败: {str(e)}")

    # 新增：加载工程文件到下拉框
    def load_project_files(self, project_name, episode_number, shot_name):
        """加载指定目录下的.nk工程文件，并按版本号降序排列"""
        self.cmb_file.clear()
        self.cmb_file.addItem("- 工程文件选择 -", None)
        self.cmb_file.setEnabled(False)
        
        # 检查必要参数
        if not all([project_name, episode_number, shot_name]):
            return
            
        # 构建目标路径
        file_path = f"W:/Project/{project_name}/shot_work/{episode_number}/{shot_name}/task/comp/Nuke/master/"
        
        try:
            # 检查路径是否存在
            if not os.path.exists(file_path):
                return
                
            # 获取所有.nk文件（仅文件，排除文件夹）
            nk_files = []
            for item in os.listdir(file_path):
                item_path = os.path.join(file_path, item)
                if os.path.isfile(item_path) and item.endswith(".nk"):
                    nk_files.append(item)
            
            # 按版本号排序（假设文件名包含版本号如v0001）
            # 提取版本号并按降序排序
            def extract_version(filename):
                # 尝试从文件名中提取版本号数字（支持v+数字格式）
                import re
                match = re.search(r'v(\d+)', filename, re.IGNORECASE)
                if match:
                    return int(match.group(1))
                return 0  # 没有版本号的放最后
            
            # 按版本号降序排列
            nk_files.sort(key=extract_version, reverse=True)
            
            # 添加到下拉框
            for file in nk_files:
                self.cmb_file.addItem(file, os.path.join(file_path, file))
                
            if len(nk_files) > 0:
                self.cmb_file.setEnabled(True)
                
        except Exception as e:
            self._show_error("文件加载错误", f"加载工程文件失败: {str(e)}")

    # 新增：工程文件选择变化事件
    def on_file_changed(self, index):
        file_path = self.cmb_file.currentData()
        if file_path and os.path.exists(file_path):
            try:
                pass
            except Exception as e:
                self._show_error("失败", f"无法显示工程文件: {str(e)}")

    # 新增：显示关闭项目复选框状态变化处理
    def on_show_closed_changed(self, state):
        self.show_closed_projects = (state == QtCore.Qt.Checked)
        # 重新加载项目列表
        self.cmb_project.clear()
        self.cmb_episode.clear()
        self.cmb_shot.clear()
        self.cmb_file.clear()  # 新增：清空工程文件
        self.cmb_episode.setEnabled(False)
        self.cmb_shot.setEnabled(False)
        self.cmb_file.setEnabled(False)  # 新增：禁用工程文件
        self.lbl_creator.setText("Artist: ---")
        self.lbl_production_status.setText("制作阶段状态: ---")
        self.lbl_nb_shenhe.setText("内部审核状态: ---")
        self.lbl_kh_shenhe.setText("客户审核状态: ---")
        self.lbl_review_message.setText("反馈内容: ---")
        self.load_projects()

    def on_creator_changed(self):
        self.cmb_project.clear()
        self.cmb_episode.clear()
        self.cmb_shot.clear()
        self.cmb_file.clear()  # 新增：清空工程文件
        self.cmb_episode.setEnabled(False)
        self.cmb_shot.setEnabled(False)
        self.cmb_file.setEnabled(False)  # 新增：禁用工程文件
        self.lbl_creator.setText("Artist: ---")
        self.lbl_production_status.setText("制作阶段状态: ---")
        self.lbl_nb_shenhe.setText("内部审核状态: ---")
        self.lbl_kh_shenhe.setText("客户审核状态: ---")
        self.lbl_review_message.setText("反馈内容: ---")
        self.load_projects()

    def on_project_changed(self, index):
        self.cmb_episode.setEnabled(False)
        self.cmb_shot.setEnabled(False)
        self.cmb_file.setEnabled(False)  # 新增：禁用工程文件
        self.cmb_episode.clear()
        self.cmb_shot.clear()
        self.cmb_file.clear()  # 新增：清空工程文件
        self.lbl_creator.setText("Artist: ---")
        self.lbl_production_status.setText("制作阶段状态: ---")
        self.lbl_nb_shenhe.setText("内部审核状态: ---")
        self.lbl_kh_shenhe.setText("客户审核状态: ---")
        self.lbl_review_message.setText("反馈内容: ---")

        project_id = self.cmb_project.currentData()
        if not project_id:
            return

        creator = self.cmb_creator.currentData()
        try:
            with self.db_conn.cursor() as cursor:
                if creator and creator != "未分配" and creator != "全部":
                    cursor.execute("""
                        SELECT e.id, e.number 
                        FROM tb_episodes e
                        JOIN tb_shotdata sd ON e.id = sd.episodes_id
                        JOIN tb_shotinfo si ON sd.id = si.shot_id
                        WHERE e.project_id = %s AND si.creator LIKE %s
                        GROUP BY e.id
                        ORDER BY e.number
                    """, (project_id, '%' + creator + '%'))
                else:
                    cursor.execute("""
                        SELECT id, number 
                        FROM tb_episodes 
                        WHERE project_id = %s
                        ORDER BY number
                    """, (project_id,))
                episodes = cursor.fetchall()

                self.cmb_episode.addItem("- 集数选择 -", None)
                for ep in episodes:
                    self.cmb_episode.addItem(f"{ep['number']}", ep['id'])
                self.cmb_episode.setEnabled(True)

        except Exception as e:
            self._show_error("Data Error", f"加载集数失败: {str(e)}")

    def on_episode_changed(self, index):
        self.cmb_shot.setEnabled(False)
        self.cmb_file.setEnabled(False)  # 新增：禁用工程文件
        self.cmb_shot.clear()
        self.cmb_file.clear()  # 新增：清空工程文件
        self.lbl_creator.setText("Artist: ---")
        self.lbl_production_status.setText("制作阶段状态: ---")
        self.lbl_nb_shenhe.setText("内部审核状态: ---")
        self.lbl_kh_shenhe.setText("客户审核状态: ---")
        self.lbl_review_message.setText("反馈内容: ---")

        episode_id = self.cmb_episode.currentData()
        if not episode_id:
            return

        creator = self.cmb_creator.currentData()
        try:
            with self.db_conn.cursor() as cursor:
                if creator and creator != "未分配" and creator != "全部":
                    cursor.execute("""
                        SELECT s.id, s.shot_name, s.total_frames
                        FROM tb_shotdata s
                        JOIN tb_shotinfo si ON s.id = si.shot_id
                        WHERE s.episodes_id = %s AND si.creator LIKE %s
                        ORDER BY s.shot_name
                    """, (episode_id, '%' + creator + '%'))
                else:
                    cursor.execute("""
                        SELECT id, shot_name, total_frames
                        FROM tb_shotdata
                        WHERE episodes_id = %s
                        ORDER BY shot_name
                    """, (episode_id,))
                shots = cursor.fetchall()

                self.cmb_shot.addItem("- 镜头选择 -", None)
                for shot in shots:
                    text = f"{shot['shot_name']} ({shot['total_frames']}帧)"
                    self.cmb_shot.addItem(text, shot['id'])
                self.cmb_shot.setEnabled(True)

        except Exception as e:
            self._show_error("Data Error", f"加载镜头失败: {str(e)}")

    def on_shot_changed(self, index):
        shot_id = self.cmb_shot.currentData()
        if not shot_id:
            self.lbl_creator.setText("Artist: ---")
            self.lbl_production_status.setText("制作阶段状态: ---")
            self.lbl_nb_shenhe.setText("内部审核状态: ---")
            self.lbl_kh_shenhe.setText("客户审核状态: ---")
            self.lbl_review_message.setText("反馈内容: ---")
            self.cmb_file.clear()
            self.cmb_file.addItem("- 工程文件选择 -", None)
            self.cmb_file.setEnabled(False)
            return

        try:
            with self.db_conn.cursor() as cursor:
                # 获取制作者信息
                cursor.execute("""
                    SELECT creator 
                    FROM tb_shotinfo 
                    WHERE shot_id = %s
                    LIMIT 1
                """, (shot_id,))
                result = cursor.fetchone()
                creator = result.get('creator', '未知') if result else '未知'
                self.lbl_creator.setText(f"Artist: {creator}")

                # 获取制作阶段状态等信息
                cursor.execute("""
                    SELECT production_status, nb_shenhe, kh_shenhe, reivew_message
                    FROM tb_shotinfo 
                    WHERE shot_id = %s
                    LIMIT 1
                """, (shot_id,))
                result = cursor.fetchone()
                production_status = result.get('production_status', '未知') if result else '未知'
                nb_shenhe = result.get('nb_shenhe', '未知') if result else '未知'
                kh_shenhe = result.get('kh_shenhe', '未知') if result else '未知'
                review_message = result.get('reivew_message', '未知') if result else '未知'

                self.lbl_production_status.setText(f"制作阶段状态: {production_status}")
                self.lbl_nb_shenhe.setText(f"内部审核状态: {nb_shenhe}")
                self.lbl_kh_shenhe.setText(f"客户审核状态: {kh_shenhe}")
                self.lbl_review_message.setText(f"反馈内容: {review_message}")

                # 获取项目名、集数和镜头名用于加载工程文件
                project_id = self.cmb_project.currentData()
                episode_id = self.cmb_episode.currentData()
                
                # 获取项目名
                cursor.execute("SELECT project_name FROM tb_projects WHERE id = %s", (project_id,))
                project_data = cursor.fetchone()
                project_name = project_data['project_name'] if project_data else None
                
                # 获取集数
                cursor.execute("SELECT number FROM tb_episodes WHERE id = %s", (episode_id,))
                episode_data = cursor.fetchone()
                episode_number = episode_data['number'] if episode_data else None
                
                # 获取镜头名
                cursor.execute("SELECT shot_name FROM tb_shotdata WHERE id = %s", (shot_id,))
                shot_data = cursor.fetchone()
                shot_name = shot_data['shot_name'] if shot_data else None

                # 加载工程文件
                self.load_project_files(project_name, episode_number, shot_name)

            # 检查项目、集数、镜头是否都有有效数据
            project_id = self.cmb_project.currentData()
            episode_id = self.cmb_episode.currentData()
            if project_id and episode_id and shot_id:
                # 暂时断开信号连接，避免触发on_creator_changed导致数据清空
                self.cmb_creator.currentIndexChanged.disconnect(self.on_creator_changed)
                # 将制作者设为"全部"（第一个选项，索引为0）
                self.cmb_creator.setCurrentIndex(0)
                # 重新连接信号
                self.cmb_creator.currentIndexChanged.connect(self.on_creator_changed)

        except Exception as e:
            self._show_error("Query Error", f"获取信息失败: {str(e)}")

    def on_test_button_1_clicked(self):
        # 检查是否选择了项目、集数和镜头
        project_id = self.cmb_project.currentData()
        episode_id = self.cmb_episode.currentData()
        shot_id = self.cmb_shot.currentData()
        
        if not all([project_id, episode_id, shot_id]):
            nuke.message("请先选择完整的项目、集数和镜头信息")
            return

        try:
            # 从数据库获取项目名、集数和镜头号的原始数据
            with self.db_conn.cursor() as cursor:
                # 获取项目名
                cursor.execute("SELECT project_name FROM tb_projects WHERE id = %s", (project_id,))
                project_name = cursor.fetchone()['project_name']
                
                # 获取集数
                cursor.execute("SELECT number FROM tb_episodes WHERE id = %s", (episode_id,))
                episode_number = cursor.fetchone()['number']
                
                # 获取镜头名
                cursor.execute("SELECT shot_name FROM tb_shotdata WHERE id = %s", (shot_id,))
                shot_name = cursor.fetchone()['shot_name']

            # 构建基础路径
            base_path = f"W:/Project/{project_name}/shot_work/{episode_number}/{shot_name}/task/comp/Nuke/master"
            # 创建目录（如果不存在）
            os.makedirs(base_path, exist_ok=True)

            # 处理版本号：查找当前最大版本号
            prefix = f"{shot_name}_comp_master_v"
            max_version = 0
            for filename in os.listdir(base_path):
                if filename.startswith(prefix) and filename.endswith(".nk"):
                    try:
                        version_str = filename[len(prefix):-3]  # 提取v后面的数字部分
                        version = int(version_str)
                        if version > max_version:
                            max_version = version
                    except ValueError:
                        continue

            # 计算新版本号
            new_version = max_version + 1
            version_str = f"v{new_version:04d}"  # 格式化为4位数字，如v0001
            file_name = f"{shot_name}_comp_master_{version_str}.nk"
            full_path = os.path.join(base_path, file_name)

            # 创建新的Nuke脚本并保存
            nuke.scriptClear()  # 清除当前脚本
            nuke.scriptSaveAs(full_path)  # 保存新脚本
            
            # 打开创建的脚本
            nuke.scriptOpen(full_path)
            
            # 重新加载工程文件列表
            self.load_project_files(project_name, episode_number, shot_name)
            
            nuke.message(f"成功创建并打开工程文件：\n{full_path}")

        except Exception as e:
            self._show_error("创建工程失败", f"错误信息：{str(e)}")

    def on_test_button_2_clicked(self):
        import nuke
        import nukescripts
        import projectManager_main as PMM

        PMM.add_projectManager_to_panel()

        nuke.scriptSave()



    def on_open_selected_clicked(self):
        """打开选中的工程文件"""
        file_path = self.cmb_file.currentData()
        if not file_path or not os.path.exists(file_path):
            nuke.message("未选中任何工程文件或文件不存在")
            return
        
        try:
            # 关闭当前脚本(可选)
            # nuke.scriptClear()
            # 打开选中的工程文件
            nuke.scriptOpen(file_path)
            nuke.message(f"成功打开工程文件：\n{file_path}")
        except Exception as e:
            self._show_error("打开失败", f"无法打开工程文件: {str(e)}")

    def on_add_cmd_render_clicked(self):
        """显示CMD渲染设置窗口"""
        if not self.cmb_file.currentData():
            self._show_error("错误", "请先选择工程文件")
            return
            
        # 显示渲染设置窗口
        render_window = RenderSettingsWindow(self)
        render_window.exec_()











    def _show_error(self, title, message):
        """Nuke风格错误提示"""
        error_dialog = QtWidgets.QMessageBox(self)
        error_dialog.setStyleSheet(self.NUKE_STYLE)
        error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        error_dialog.setWindowTitle(title)
        error_dialog.setText(message)
        error_dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        error_dialog.exec_()

    def closeEvent(self, event):
        if self.db_conn:
            try:
                self.db_conn.close()
            except:
                pass
        event.accept()

    # 新增：匹配按钮点击事件处理（更新版）
    def on_match_clicked(self):
        """匹配按钮功能：只显示匹配到的工程文件信息，不打开"""
        # 获取当前选择的项目、集数、镜头信息
        project_id = self.cmb_project.currentData()
        episode_id = self.cmb_episode.currentData()
        shot_id = self.cmb_shot.currentData()
        
        if not all([project_id, episode_id, shot_id]):
            nuke.message("请先选择完整的项目、集数和镜头信息")
            return
        
        # 获取项目名称、集数、镜头名（根据你的数据库结构调整查询语句）
        try:
            with self.db_conn.cursor() as cursor:
                # 获取项目名称
                cursor.execute("SELECT project_name FROM tb_projects WHERE id = %s", (project_id,))
                project_name = cursor.fetchone()['project_name']
                
                # 获取集数
                cursor.execute("SELECT number FROM tb_episodes WHERE id = %s", (episode_id,))
                episode_number = cursor.fetchone()['number']
                
                # 获取镜头名
                cursor.execute("SELECT shot_name FROM tb_shotdata WHERE id = %s", (shot_id,))
                shot_name = cursor.fetchone()['shot_name']
                
                # 加载匹配的工程文件
                self.load_project_files(project_name, episode_number, shot_name)
                
                # 显示匹配结果
                file_count = self.cmb_file.count() - 1  # 减去默认项
        except Exception as e:
            self._show_error("匹配错误", f"匹配过程中发生错误: {str(e)}")

# 独立窗口启动函数
def show_project_browser():
    global browser_window
    try:
        browser_window.close()
    except:
        pass
    browser_window = NukeStyleProjectBrowser()
    browser_window.show()

# 注册为Nuke菜单命令
nuke.menu("Nuke").addCommand("projectManager/Project浏览器v1.2", show_project_browser)
