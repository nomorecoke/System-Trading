import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3

TR_REQ_TIME_INTERVAL = 0.2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()
        self.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        print("set")
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)
        self.OnReceiveConditionVer.connect(self._receive_condition_ver)
        self.OnReceiveTrCondition.connect(self._receive_condition_data)

    def _receive_condition_ver(self, iRet, sMsg):
        a = self.dynamicCall("GetConditionNameList()")
        print (a)
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _receive_condition_data(self,screen_no, code_list, condition_name, index, next):
        code_list= code_list.split(';')
        self.condition_output =  code_list[:-1]
        print(self.condition_output)
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()



    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    #전일 종가
    def get_master_last_price(self, code):
        last_price = self.dynamicCall("GetMasterLastPrice(QString)", code)
        return last_price

    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)

        elif rqname == "opt10080_req":
            self._opt10080(rqname, trcode)

        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)

        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10080(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        check_1520 = 0
        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "체결시간")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            #초단위는 필요없다 뒤에 2자리 절사
            self.ohlcv['date'].append(date[:-2])
            self.ohlcv['open'].append(abs(int(open)))
            self.ohlcv['high'].append(abs(int(high)))
            self.ohlcv['low'].append(abs(int(low)))
            self.ohlcv['close'].append(abs(int(close)))
            self.ohlcv['volume'].append(abs(int(volume)))


    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(abs(int(open)))
            self.ohlcv['high'].append(abs(int(high)))
            self.ohlcv['low'].append(abs(int(low)))
            self.ohlcv['close'].append(abs(int(close)))
            self.ohlcv['volume'].append(abs(int(volume)))



        #판다스를 이용하여 저장
        #df = pd.DataFrame(kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=kiwoom.ohlcv['date'])


    # send order added 0521
    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        # status -330 : 주문 넣었는데 안들어간경우
        status = -330
        while status == -330:
            status = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                      [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])
            # check for success
            print("status", status)

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        # print("...")
        # need to clear daily
        f = open("data/chejan.txt", 'a')
        if gubun == 0 :
            print("주문 체결")
        elif gubun == 1:
            print("잔고 통보")
        #print(self.get_chejan_data(9203))
        print("\n913 : ",self.get_chejan_data(913))
        print("\n수량",self.get_chejan_data(900))
        print("\n가격",self.get_chejan_data(901))
        print("\n매수 매도", self.get_chejan_data(905))
        print("\n매수 매도", self.get_chejan_data(907))
        print("\n10번 정보", self.get_chejan_data(10))

        f.close()


    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    # 05-23  added
    # 예수금 조회
    def _opw00001(self, rqname, trcode):
        d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)


    # 잔고 조회
    def _opw00018(self, rqname, trcode):
        # single data
        total_purchase_price = self._comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산")

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))

        total_earning_rate = Kiwoom.change_format2(total_earning_rate)
        # 모의 투자와 실투의 출력양식차이
        '''
        if self.get_server_gubun():
            total_earning_rate = float(total_earning_rate) / 100
            total_earning_rate = str(total_earning_rate)
        '''
        self.opw00018_output['single'].append(total_earning_rate)

        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))

        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            code_num = self._comm_get_data(trcode, "", rqname, i, "종목번호")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")

            quantity = Kiwoom.change_format(quantity)
            code_num = Kiwoom.change_format3(code_num)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)
            print(name, code_num, quantity, purchase_price, current_price, eval_profit_loss_price, earning_rate)
            #print(name, ":", code_num)
            self.opw00018_output['multi'].append(
                [name, code_num, quantity, purchase_price, current_price, eval_profit_loss_price, earning_rate])

    def reset_ohlcv(self):
        self.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

    def reset_condition_output(self):
        self.condition_output = []

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    # change money format
    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '':
            strip_data = '0'
        format_data = format(int(strip_data), ',d')

        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data

    # 수익률 format
    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data

    # 종목코드 format
    @staticmethod
    def change_format3(data):
        strip_data = data.lstrip('-A')
        return strip_data

    # 05 29 added : 조건검색
    def get_condition(self, screen_no, condition_name, condition_index, search_type): #search type --> 0: 그냥 검색, 1: 실시간 검색

        status = self.dynamicCall("SendCondition(QString, QString, int, int)",
                                  [screen_no, condition_name, condition_index, search_type])
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()
        return status

    def call_day_chart(self, code, date, modify):
        self.set_input_value('종목코드', code)
        self.set_input_value('기준일자', date)
        self.set_input_value('수정주가구분', modify)
        self.comm_rq_data("opt10081_req", "opt10081", 0, "0101")
        while self.remained_data == True:
            # 1초에 최대 5건 받기가능 안전하게 4건으로
            time.sleep(0.25)
            self.set_input_value('종목코드', code)
            self.set_input_value('기준일자', date)
            self.set_input_value('수정주가구분', modify)
            self.comm_rq_data("opt10081_req", "opt10081", 2, "0101")

    def call_minute_chart(self, code, tick_range, modify):
        self.set_input_value('종목코드', code)
        self.set_input_value('틱범위', tick_range)
        self.set_input_value('수정주가구분', modify)
        self.comm_rq_data("opt10080_req", "opt10080", 0, "0101")
        while self.remained_data == True:
            # 1초에 최대 5건 받기가능 안전하게 4건으로
            time.sleep(0.25)
            self.set_input_value('종목코드', code)
            self.set_input_value('틱범위', tick_range)
            self.set_input_value('수정주가구분', modify)
            self.comm_rq_data("opt10080_req", "opt10080", 2, "0101")


# For test
if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    kiwoom.reset_opw00018_output()
    kiwoom.reset_condition_output()
    kiwoom.reset_ohlcv()
    account_number = kiwoom.get_login_info("ACCNO")
    account_number = account_number.split(';')[0]

    kiwoom.dynamicCall("GetConditionLoad()")
    kiwoom.tr_event_loop = QEventLoop()
    kiwoom.tr_event_loop.exec_()

    kiwoom.set_input_value("계좌번호", account_number)
    kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

    print(kiwoom.opw00018_output['single'])
    print(kiwoom.opw00018_output['multi'])
    #전일 종가..
    print("가격 : ", kiwoom.get_master_last_price("011080"))
    kiwoom.call_day_chart("004140", "20180604", 1)



    print(kiwoom.ohlcv)
    # 8104749811 <- 1억
    # 8105084911 <- 천만원
