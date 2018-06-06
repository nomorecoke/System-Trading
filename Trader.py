import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
import os
from datetime import datetime
import codecs


# 계좌번호 8104749811
form_class = uic.loadUiType("pytrader.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        # 한번에 한 종목에 들어갈 돈 세팅
        self.one_buy_money = 10000000

        self.setupUi(self)
        self.load_data_lock = False
        self.trade_stocks_done = False
        self.choose_buy_done = False
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()


        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        self.lineEdit.textChanged.connect(self.code_changed)
        self.pushButton_2.clicked.connect(self.check_balance)

        self.load_buy_sell_list()


        # Timer2
        self.timer2 = QTimer(self)
        #3 sec로 세팅 ms단위
        self.timer2.start(1000 * 10)
        self.timer2.timeout.connect(self.timeout2)



        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")
        accounts_list = accounts.split(';')[0:accouns_num]
        self.comboBox.addItems(accounts_list)

        self.pushButton.clicked.connect(self.send_order)
        # 처음에 조회
        self.check_balance()
        self.kiwoom.dynamicCall("GetConditionLoad()")
        self.kiwoom.tr_event_loop = QEventLoop()
        self.kiwoom.tr_event_loop.exec_()



    # 0529 - YW : 자동으로 검색식에 있는 종목을 매수 설정한다.
    # sell은 잔고자동편입을 이용한다.
    # algorithm 조건 식 종류 선택
    def choose_buy(self, algorithm):
        # 화면번호, 조건식명, 조건식 index, 0: 정적조회, 1: 실시간 조회
        print("choose buy")
        self.kiwoom.reset_condition_output()

        # 처음은 종가과매수만 진행할 예정
        if algorithm == 0:
            self.kiwoom.get_condition("0156","S_종가과매수",0,0)
        # 05 29 add for test
        elif algorithm == 1:
            self.kiwoom.get_condition("0156", "무패신호", 7, 0)

        # self.kiwoom.condition_output에 종목코드가 list로 들어가 있음

        # make buy_list file
        f = codecs.open("data/buy_list.txt", 'w', 'utf-8')
        log = codecs.open("data/log_file.txt", 'a', 'utf-8')
        now = datetime.now()
        log.write('\n%s-%s-%s %s:%s\n' %(now.year, now.month, now.day, now.hour, now.minute))
        self.load_data_lock = True
        for i in self.kiwoom.condition_output:
            #일단은 시장가매수

            name = self.kiwoom.get_master_code_name(i)
            last_price = int(self.fetch_chart_data(i))
            order_number = int(self.one_buy_money/last_price)
            order_price = last_price
            log.write("%s, %s, %s원, %s주, %d만원 \n" % (i, name,last_price, order_number, last_price*order_number/10000))
            f.write("매수,%s,시장가,%d,%d,매수전\n" %(i,order_number,order_price))
        f.close()
        log.close()
        self.load_data_lock = False

    #종목 코드 기준 날짜
    #기준 날짜부터 과거까지 순서로 조회한다. but 지금은 당일 data만 필요
    def fetch_chart_data(self, code_num):
        self.kiwoom.reset_ohlcv()
        base_date = datetime.today().strftime('%Y%m%d')
        self.kiwoom.call_day_chart(code_num, base_date, 1)
        # 판다스를 이용하여 저장
        df = pd.DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=self.kiwoom.ohlcv['date'])
        return df.ix[base_date]["close"]



    def trade_stocks(self):
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        f = codecs.open("data/buy_list.txt", 'r','utf-8')
        buy_list = f.readlines()
        f.close()

        f = codecs.open("data/sell_list.txt", 'r', 'utf-8')
        sell_list = f.readlines()
        f.close()

        # account
        account = self.comboBox.currentText()

        # buy list
        for row_data in buy_list:
            split_row_data = row_data.split(',')
            try:
                hoga = split_row_data[2]
            except:
                break
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매수전':
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, price,
                                       hoga_lookup[hoga], "")

        # sell list
        for row_data in sell_list:
            split_row_data = row_data.split(',')
            try:
                hoga = split_row_data[2]
            except:
                break
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매도전':
                self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, price,
                                       hoga_lookup[hoga], "")

        # buy list
        for i, row_data in enumerate(buy_list):
            buy_list[i] = buy_list[i].replace("매수전", "주문완료")

        # file update
        f = codecs.open("data/buy_list.txt", 'w','utf-8')
        for row_data in buy_list:
            f.write(row_data)
        f.close()

        # sell list
        for i, row_data in enumerate(sell_list):
            sell_list[i] = sell_list[i].replace("매도전", "주문완료")

        # file update
        f = codecs.open("data/sell_list.txt", 'w','utf-8')
        for row_data in sell_list:
            f.write(row_data)
        f.close()

    def load_buy_sell_list(self):
        f = codecs.open("data/buy_list.txt", "r","utf-8")
        buy_list = f.readlines()
        f.close()

        f = codecs.open("data/sell_list.txt", "r","utf-8")
        sell_list = f.readlines()
        f.close()

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_3.setRowCount(row_count)

        # buy list
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(',')
            try:
                split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip())
            except:
                break

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                if i == 0:
                    item.setForeground(Qt.red)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(j, i, item)

        # sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(',')
            try:
                split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip())
            except:
                break

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                if i == 0:
                    item.setForeground(Qt.blue)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(len(buy_list) + j, i, item)

        self.tableWidget_3.resizeRowsToContents()

    def timeout(self):
        # 9시 1분에 주문넣기
        market_start_time = QTime(9, 1, 0)
        market_end_time = QTime(15,30,0)
        current_time = QTime.currentTime()

        if market_start_time < current_time < market_end_time and self.trade_stocks_done is False:
            self.trade_stocks_done = True
            self.trade_stocks()
            self.trade_stocks_done = False
        #3시 10분 종목선정~

        if QTime(15, 10 ,0) < current_time  and self.choose_buy_done is False:
            self.choose_buy(0)
            self.choose_buy_done = True

        # 오후 6시 프로그램 자동 종료
        if current_time > QTime(18,00,0) :
            print("End program")
            self.quit()

        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.get_connect_state()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"

        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def code_changed(self):
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    def send_order(self):
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        account = self.comboBox.currentText()
        order_type = self.comboBox_2.currentText()
        code = self.lineEdit.text()
        hoga = self.comboBox_3.currentText()
        num = self.spinBox.value()
        price = self.spinBox_2.value()
        #print(account, order_type,code,hoga,num,price)
        #print(order_type_lookup[order_type],hoga_lookup[hoga] )
        self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, num, price,
                               hoga_lookup[hoga],"")

    def timeout2(self):
        #연속조회시 transaction 충돌로 starvation이 걸림
        if self.load_data_lock is False :
            #체크 하지 않아도 system trading 업데이트
            self.load_buy_sell_list()
            #check 했을 때 만 자동 조회
            if self.checkBox.isChecked():
                self.check_balance()

    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]
        account_number = self.comboBox.currentText()

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        # opw00001
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        # balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)
        #single
        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])

            if i == 3 or i == 4:
                if item.text().startswith('-'):
                    item.setForeground(Qt.blue)
                else:
                    item.setForeground(Qt.red)

            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)

        self.tableWidget.resizeRowsToContents()

        # multi Item list
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                if i ==  len(row) - 1 or i == len(row) - 2 :
                    if item.text().startswith('-'):
                        item.setForeground(Qt.blue)
                    else:
                        item.setForeground(Qt.red)

                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

        self.tableWidget_2.resizeRowsToContents()



if __name__ == "__main__":
    current_time = QTime.currentTime()
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()

    log = codecs.open("data/log_file.txt", 'a', 'utf-8')
    log.write("시작")
    now = datetime.now()
    log.write('\n%s-%s-%s %s:%s\n' % (now.year, now.month, now.day, now.hour, now.minute))
    log.close()

    f = open("data/chejan.txt", 'w')
    f.write('\n%s-%s-%s %s:%s\n' % (now.year, now.month, now.day, now.hour, now.minute))
    f.close()

    sys.exit(app.exec_())
    log = codecs.open("data/log_file.txt", 'a', 'utf-8')
    log.write("종료")
    now = datetime.now()
    log.write('\n%s-%s-%s %s:%s\n' % (now.year, now.month, now.day, now.hour, now.minute))
    log.close()






