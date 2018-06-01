# System-Trading

개인 조건검색식과 키움API를 활용한 system trader입니다.

Trader.py : trading 알고리즘이 들어있는 파일



작동 알고리즘은 다음과 같다.

윈도우 작업 스케쥴러를 활용하여 작동한다.


오전 8시 -> Update.py를 실행: 번개3를 작동시키고 업데이트를 진행
오전 9시 -> Trader.py를 실행: open api를 활용하여 buy_list.txt에 매수 종목 저장 및 매수

05/31 - log파일을 작성하여 작업 스케쥴러의 작동을 확인
06/01 - 매수 알고리즘 수정 및 git upload
