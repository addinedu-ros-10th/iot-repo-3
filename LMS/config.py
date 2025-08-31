# config.py : 파라미터 관련 파일 / 하드코딩 방지

# TCP/IP 소켓통신 설정 (네트워크 3계층)
TCP_PROTOCOL_CONFIG = {
  # 1. 기본설정
  'host' : 'localhost',
  'port' : 8100,
  
  # 2. 메시지 형식 관련 변수 설정
  'message_size' : 17,        # Command + Data + End 사이즈
  'message_header_size' : 2,  # Command 사이즈
  'message_data_size' : 14,   # Data 사이즈
  'message_end_size' : 1,     # End 사이즈

  # 3. 통신 관련 설정
  'max_message' : 10, # TCP 핸들러는 최대 10개의 값을 읽어올 수 있음

}

# 시리얼 소켓통신 설정 (네트워크 1계층)
SERIAL_PROTOCOL_CONFIG = {
  'device' : '/dev/ttyACM0',
  'baud_rate' : 9600,
}
