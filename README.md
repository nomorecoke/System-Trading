# System-Trading

개인 조건검색식과 키움API를 활용한 system trader입니다.

Trader.py : trading 알고리즘 , UI 연결 ,  주문 

Kiwoom.py : kiwoom API와 통신



## 작동 알고리즘 ##
윈도우 작업 스케쥴러를 활용하여 작동한다.

오전 8시 -> Update.py를 실행: 번개3를 작동시키고 업데이트를 진행

오전 9시 -> Trader.py를 실행: open api를 활용하여 buy_list.txt에 매수 종목 저장 및 buy_list , sell_list 를 읽어와 주문


## 업데이트 내역 ##
05/31 - log파일을 작성하여 작업 스케쥴러의 작동을 확인

06/01 - 매수 알고리즘 수정 및 git upload

06/05 - 버그 수정, opsen high low close volumn data 받아와서 pandas를 이용하여 저장 

07/11 - 매수 알고리즘 수정 - 스캘핑 봇으로 변경(코드 비공개)

07/13 - 실제 계좌로 test 수행 , 시장가 매수시 가격란에 0을 입력하지 않으면 error 발생함

