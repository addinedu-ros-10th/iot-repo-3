# 메시지 프로토콜 패킹/언패킹 클래스 데모

import struct

"""
@staticmethod : 클래스라는 이름 공간(Namespace)에 속해있는 일반 함수 정의 데코레이터
클래스 인스턴스 생성 없이도 이름공간 클래스에 접근하면 메서드를 사용할 수 있다.
"""

class MessageProtocol:
  """
  LMS 메시지 프로토콜 클래스
  
  기능 :
  
  """
  
  @staticmethod
  def pack_command(command : str, data : bytes) -> bytes:
    """명령어를 17바이트 바이너리로 패킹"""
    # ljust(width, fillchar) : 문자열을 왼쪽으로 정렬하고, 남는 공간을 fillchar으로 채움
    cmd_bytes = command.encode('ascii')[:2].ljust(2, b'\x00')
    data_bytes = data[:14].ljust(14, b'\x00') # 14 바이트로 고정
    end_byte = b'\n'
    
    return cmd_bytes + data_bytes + end_byte
  
  """
  struct.pack(fmt : str | bytes, / , *v: Any) -> bytes
  fmt 예시 : '<HH' / '<HHH' / '<B'
  
  '<바이트 순서><데이터 타입 문자>'
  '<HH' : 바이트 순서 리틀 엔디안 / 데이터 타입 : H unsigned short
  
  B : 1바이트, int, unsigned char
  H : 2바이트, int, unsigned short
  i : 4바이트, int, int
  """
  
  # 데이터 패킹, return : 14 Byte
  @staticmethod
  def pack_ri_data(receive : int) -> bytes:
    """RI 명령어 데이터 패킹 : RECEIVE (2Byte) + padding (12Byte)"""
    return struct.pack('<H', receive) + b'\x00' * 14
  
  # dict을 인자로 받음
  @staticmethod
  def pack_au_data(stock_info : dict) -> bytes:
    """AU 명령어 데이터 패킹 (재고 정보 dict)"""
    return struct.pack('<HHHHHHH',
      stock_info.get('receiving', 0),
      stock_info.get('red_storage', 0),
      stock_info.get('green_storage', 0),
      stock_info.get('yellow_storage', 0),
      stock_info.get('shipping', 0),
      stock_info.get('receiving_total', 0),
      stock_info.get('shipping_total', 0)
    )
  
  @staticmethod
  def pack_rh_data(success : bool) -> bytes:
    """RH 명령어 데이터 패킹 : SUCCESS (1Byte) + padding (13Byte)"""
    return struct.pack('<H', success) + b'\x00' * 14
  
  @staticmethod
  def pack_si_data(red : int, green : int, yellow : int) -> bytes:
    """SI 명령어 데이터 패킹 : RED (2Byte) + GREEN (2Byte) + YELLOW (2Byte) + padding (8Byte)"""
    return struct.pack('<HHH', red, green, yellow) + b'\x00' * 8
  
  @staticmethod
  def pack_ra_data() -> bytes:
    """RA 명령어 데이터 패킹 : 빈 데이터 (14Byte)"""
    return b'\x00' * 14
  
  # 응답 -> dict 파싱 메소드
  @staticmethod
  def unpack_response(response : bytes) -> dict:
    """
    응답을 파싱하여 딕셔너리로 반환
    응답 형식 : Command(2) + Status(1) + End(1)
    """
    if len(response) < 4:
      return {"error" : "응답 길이 부족"}

    command = response[:2].decode('ascii').rstrip('\x00')
    status = response[2]
    
    status_map = {
      0x00 : "SUCCESS",
      0x01 : "FAILURE",
      0x02 : "INVALID_CMD",
      0x03 : "INVALID_DATA"
    }
    
    return {
      "command" : command,
      "status" : status_map.get(status, f"UNKNOWN({status})")
    }
  
  # AU 명령 재고 데이터 -> dict 파싱 메소드
  @staticmethod
  def unpack_stock_data(data : bytes) -> dict:
    """14바이트 재고 데이터를 딕셔너리로 변환"""
    if len(data) < 14:
      return {"error" : "재고 데이터 길이 부족"}
    
    stock = struct.unpack('<HHHHHHH', data)
    return {
      'receiving': stock[0],
      'red_storage': stock[1],
      'green_storage': stock[2], 
      'yellow_storage': stock[3],
      'shipping': stock[4],
      'receiving_total': stock[5],
      'shipping_total': stock[6]
    }