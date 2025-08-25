# TCP 서버 메시지 처리 데모

import struct
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import PROTOCOL_CONFIG
from communication.message_protocol import MessageProtocol

class MessageHandlerDemo:
    """메시지 처리 데모"""
    
    def __init__(self):
        self.name = "Message Handler Demo"
    
    def demo_message_parsing(self):
        """메시지 파싱 데모"""
        print("=== 메시지 파싱 데모 ===")
        
        # 가상 RI 메시지 생성 (RED=5, GREEN=3)
        ri_data = MessageProtocol.pack_ri_data(5, 3)
        ri_message = MessageProtocol.pack_command('RI', ri_data)
        
        print(f"RI 메시지 생성: {ri_message.hex()}")
        print(f"메시지 길이: {len(ri_message)}바이트")
        
        # 메시지 파싱
        if len(ri_message) == 17:
            command = ri_message[:2].decode('ascii').rstrip('\x00')
            data = ri_message[2:16]
            end_byte = ri_message[16]
            
            print(f"파싱 결과:")
            print(f"  명령어: {command}")
            print(f"  데이터: {data.hex()}")
            print(f"  종료바이트: 0x{end_byte:02X}")
            
            if command == 'RI':
                red, green = struct.unpack('<HH', data[:4])
                print(f"  입고요청: RED={red}, GREEN={green}")
    
    def demo_response_creation(self):
        """응답 생성 데모"""
        print("\n=== 응답 생성 데모 ===")
        
        # 성공 응답
        success_response = b'RI\x00\n'
        print(f"성공 응답: {success_response.hex()}")
        
        # 실패 응답
        failure_response = b'RI\x01\n'  
        print(f"실패 응답: {failure_response.hex()}")
        
        # AU 응답 (재고 데이터)
        stock_data = {
            'receiving': 0,
            'red_storage': 10,
            'green_storage': 5,
            'yellow_storage': 8,
            'shipping': 2,
            'receiving_total': 50,
            'shipping_total': 30
        }
        
        au_data = MessageProtocol.pack_au_data(stock_data)
        au_message = MessageProtocol.pack_command('AU', au_data)
        print(f"AU 응답: {au_message.hex()}")
        print(f"AU 길이: {len(au_message)}바이트")
    
    def demo_client_handler_structure(self):
        """클라이언트 핸들러 구조 데모"""
        print("\n=== 클라이언트 핸들러 구조 ===")
        
        handler_steps = [
            "1. 17바이트 메시지 수신",
            "2. 명령어 파싱 (2바이트)",
            "3. 데이터 추출 (14바이트)",
            "4. 명령어별 처리 로직 호출",
            "5. 응답 생성 및 전송"
        ]
        
        for step in handler_steps:
            print(f"  {step}")
        
        print("\n지원할 명령어:")
        commands = ['RI', 'SI', 'RA', 'RH']
        for cmd in commands:
            print(f"  - {cmd}")

if __name__ == "__main__":
    demo = MessageHandlerDemo()
    demo.demo_message_parsing()
    demo.demo_response_creation() 
    demo.demo_client_handler_structure()