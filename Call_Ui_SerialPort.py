# 11:31 PM, June 30th, 2018 @ HDU Dormitory
# 串口调试助手逻辑文件
# Made by 镇长
# GitHub:  https://github.com/Oslomayor/PyQt5-Serial-Port
# 微信公众号: CrazyEngineer

import re
import sys
import time
import calendar
import binascii
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtWidgets import QApplication, QMainWindow
from Ui_SerialPort import Ui_Form
# from PyQt5.QtCore import QDate



class MyMainWindow(QMainWindow, Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QIcon('./daodao.ico'))
        # 设置实例
        self.CreateItems()
        # 设置信号与槽
        self.CreateSignalSlot()
        self.get_A = False
        self.rx_Buff = ""
        
    # 设置实例 
    def CreateItems(self):
        # Qt 串口类
        self.com = QSerialPort()
        # Qt 定时器类
        self.timer = QTimer(self) #初始化一个定时器
        self.timer.timeout.connect(self.ShowTime) #计时结束调用operate()方法
        self.timer.timeout.connect(self.rx_Buff_Process) #计时结束调用operate()方法
        self.timer.start(100) #设置计时间隔 100ms 并启动
        
    
    # 设置信号与槽
    def CreateSignalSlot(self):
        self.Com_Open_Button.clicked.connect(self.Com_Open_Button_clicked) 
        self.Com_Close_Button.clicked.connect(self.Com_Close_Button_clicked) 
        self.Send_Button.clicked.connect(self.SendButton_clicked) 
        self.Com_Refresh_Button.clicked.connect(self.Com_Refresh_Button_Clicked) 
        self.com.readyRead.connect(self.Com_Receive_Data) # 接收数据
        self.hexSending_checkBox.stateChanged.connect(self.hexShowingClicked)
        self.hexSending_checkBox.stateChanged.connect(self.hexSendingClicked)
        
    # 显示时间
    def ShowTime(self):
        self.Time_Label.setText(time.strftime("%B %d %H:%M:%S", time.localtime()))
    
    # 串口接收缓存区处理
    def rx_Buff_Process(self):
        # 从一堆串口数据中抓 100 个分析，再提取有效数据
        if len(self.rx_Buff) < 100:
            # 串口解析有效数据成功！ 强还是 Python 强啊！！！
            # re 正则表达式匹配 6M...6M，re.S 匹配换行符，re.findall() 返回一个列表
            rx_info = re.findall('(6M.*?)6M', self.rx_Buff, re.S)
            if len(rx_info) !=  0:
                # print(rx_info)
                ADC_Value = re.findall('A([0-9]{1,4})', rx_info[0])
                self.ADC_Bar.setProperty("value", int(ADC_Value[0]))
                self.ADC_Label.setText('%.4f' % (int(ADC_Value[0])/4096*3.3)+'V')
                # print(ADC_Value)
        else:
            self.rx_Buff = ""
            
    # 串口发送数据
    def Com_Send_Data(self):
        txData = self.textEdit_Send.toPlainText()
        if len(txData) == 0 :
            return
        if self.hexSending_checkBox.isChecked() == False:
            self.com.write(txData.encode('UTF-8'))
        else:
            Data = txData.replace(' ', '')
            # 如果16进制不是偶数个字符, 去掉最后一个, [ ]左闭右开
            if len(Data)%2 == 1:
                Data = Data[0:len(Data)-1]
            # 如果遇到非16进制字符
            if Data.isalnum() is False:
                QMessageBox.critical(self, '错误', '包含非十六进制数')
            try:
                hexData = binascii.a2b_hex(Data)
            except:
                QMessageBox.critical(self, '错误', '转换编码错误')
                return
            # 发送16进制数据, 发送格式如 ‘31 32 33 41 42 43’, 代表'123ABC'
            try:
                self.com.write(hexData) 
            except:
                QMessageBox.critical(self, '异常', '十六进制发送错误')
                return
                
                
    
    # 串口接收数据
    def Com_Receive_Data(self):
        try:
            rxData = bytes(self.com.readAll())
            
        except:
            QMessageBox.critical(self, '严重错误', '串口接收数据错误')
        
        if self.hexShowing_checkBox.isChecked() == False :
            try:
                # 将串口接收到的QByteArray格式数据转为bytes,  并用 UTF-8 解码
                self.textEdit_Recive.insertPlainText(rxData.decode('UTF-8'))
                # 将数据放入串口缓冲区
                self.rx_Buff += rxData.decode('UTF-8')
                
            except:
                pass
        else :
            Data = binascii.b2a_hex(rxData).decode('ascii')
            # re 正则表达式 (.{2}) 匹配两个字母
            hexStr = ' 0x'.join(re.findall('(.{2})', Data))
            # 补齐第一个 0x
            hexStr = '0x' + hexStr
            self.textEdit_Recive.insertPlainText(hexStr)
            self.textEdit_Recive.insertPlainText(' ')
            
        # 自动拉滚动条到底部，11代表底部
        # 参考  http://doc.qt.io/archives/qt-4.8/qtextcursor.html#MoveOperation-enum
        self.textEdit_Recive.moveCursor(11)
            
     
    # 串口刷新
    def Com_Refresh_Button_Clicked(self):
        self.Com_Name_Combo.clear()
        com = QSerialPort()
        com_list = QSerialPortInfo.availablePorts()
        for info in com_list:
            com.setPort(info)
            if com.open(QSerialPort.ReadWrite):
                self.Com_Name_Combo.addItem(info.portName())
                com.close()
    
    # 16进制显示按下   
    def hexShowingClicked(self):
        if self.hexShowing_checkBox.isChecked() == True:
            # 接收区换行
            self.textEdit_Recive.insertPlainText('\n')
    
    # 16进制发送按下   
    def hexSendingClicked(self):
        if self.hexSending_checkBox.isChecked() == True:
            pass
    
    # 发送按钮按下
    def SendButton_clicked(self):
        self.Com_Send_Data()

        
    # 串口 打开/关闭 按钮按下
    def Com_Open_Button_clicked(self):
        #### com Open Code here ####
        comName = self.Com_Name_Combo.currentText()
        comBaud = int(self.Com_Baud_Combo.currentText())
        self.com.setPortName(comName)
        try:
            if self.com.open(QSerialPort.ReadWrite) == False:
                QMessageBox.critical(self, '严重错误', '串口打开失败')
                return
        except:
            QMessageBox.critical(self, '严重错误', '串口打开失败')
            return
        self.Com_Close_Button.setEnabled(True)
        self.Com_Open_Button.setEnabled(False)
        self.Com_Refresh_Button.setEnabled(False)
        self.Com_Name_Combo.setEnabled(False)
        self.Com_Baud_Combo.setEnabled(False)
        self.Com_isOpenOrNot_Label.setText('  已打开')
        self.com.setBaudRate(comBaud)
    
    def Com_Close_Button_clicked(self):
        self.com.close()
        self.Com_Close_Button.setEnabled(False)
        self.Com_Open_Button.setEnabled(True)
        self.Com_Refresh_Button.setEnabled(True)
        self.Com_Name_Combo.setEnabled(True)
        self.Com_Baud_Combo.setEnabled(True)
        self.Com_isOpenOrNot_Label.setText('  已关闭')
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.show()
    sys.exit(app.exec_())
    
