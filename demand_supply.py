import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
import os
from datetime import datetime
import codecs


class Demand():
    def __init__(self):
        super().__init__()
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()
        #code_list = self.kiwoom.get_code_list_by_market(10)
        #print(code_list)

    # 10분봉차트 받아오기
    # 이 코드는 10분봉에 최적화된 데이터 보정을 가지고 있습니다.
    def fetch_minute_chart_data(self, code_num):
        self.kiwoom.reset_ohlcv()

        #10분봉
        self.kiwoom.call_minute_chart(code_num, 10, 1)
        # 판다스를 이용하여 저장
        df = pd.DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=self.kiwoom.ohlcv['date'])


        #10일치 10분봉 return
        modify_index = self.extract_date(df, 10)
        return df.ix[:modify_index]

    # 0 ~ 10일치에서만 사용가능
    # duration 전날 만큼의 시작 시간 출력
    def extract_date(self, df, duration):
        modify_index = 40*(duration-1)+10
        extract = df.index[modify_index]
        extract = extract[:-4]
        extract = extract + "0900"
        return extract


    # df = dataframe
    def calculate_demand_supply(self,code_num, df):
        #수급 지표 1
        demsup1 = 0
        demsup3 = 0
        demsup10 = 0

        df_1 = df[:self.extract_date(df,1)]
        for i in reversed(range(df_1.shape[0])):
            o = df_1.ix[i]['open']
            c = df_1.ix[i]['close']
            v = df_1.ix[i]['volume']
            if o < c :
                demsup1 += c*v
            elif o > c :
                demsup1 -= c*v
            #print(df_1.index[i],demsup1)

        # 100억 수급이 들어온 종목만
        if demsup1 >= 10000000000:
            return 1
        else :
            return 0

        #수급 지표 3
        #df_3 = df[:self.extract_date(df, 3)]
        #수급 지표 10
        #df =  df

# 10분봉 데이터 조회를 활용한 수급지표 계산 및 동시호가 종목 추가
if __name__ == "__main__":
    app = QApplication(sys.argv)
    demand = Demand()
    account_number = demand.kiwoom.get_login_info("ACCNO")
    account_number = account_number.split(';')[0]

    demand.kiwoom.dynamicCall("GetConditionLoad()")
    demand.kiwoom.tr_event_loop = QEventLoop()
    demand.kiwoom.tr_event_loop.exec_()

    demand.kiwoom.reset_condition_output()

    f= codecs.open("data/dongsi.csv","a")
    demand.kiwoom.get_condition("0156", "동시호가_저장용", 9, 0)
    for i in demand.kiwoom.condition_output :
        time.sleep(5)
        name = demand.kiwoom.get_master_code_name(i)
        df = demand.fetch_minute_chart_data(i)
        check = demand.calculate_demand_supply(i,df)
        # 100억 수급 넘는 종목 찾기
        if check == 1:
            i = "`"+i
            f.write("%s,%s\n" %(name,i) )
            print("%s : %s" %(i, name))

    f.close()






