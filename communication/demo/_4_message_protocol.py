# 메시지 프로토콜 패킹/언패킹 데모

import struct

class MessageProtocolDemo:
    """LMS 통신 프로토콜 데모"""
    
    @staticmethod
    def pack_command(command: str, data: bytes) -> bytes:
        """명령어를 17바이트 바이너리로 패킹"""
        # ljust(width, fillchar) : 
        cmd_bytes = command.encode('ascii')[:2].ljust(2, b'\x00')
        data_bytes = data[:14].ljust(14, b'\x00')  # 14바이트로 고정
        end_byte = b'\n'
        
        return cmd_bytes + data_bytes + end_byte
    
    @staticmethod
    def pack_ri_data(red: int, green: int) -> bytes:
        """RI 명령어 데이터 패킹: RED(2B) + GREEN(2B) + 나머지(10B)"""
        return struct.pack('<HH', red, green) + b'\x00' * 10
    
    @staticmethod
    def pack_si_data(red: int, green: int, yellow: int) -> bytes:
        """SI 명령어 데이터 패킹: RED(2B) + GREEN(2B) + YELLOW(2B) + 나머지(8B)"""
        return struct.pack('<HHH', red, green, yellow) + b'\x00' * 8
    
    @staticmethod
    def pack_rh_data(success: bool) -> bytes:
        """RH 명령어 데이터 패킹: SUCCESS(1B) + 나머지(13B)"""
        return struct.pack('<B', 1 if success else 0) + b'\x00' * 13
    
    @staticmethod
    def pack_ra_data() -> bytes:
        """RA 명령어 데이터 패킹: 빈 데이터(14B)"""
        return b'\x00' * 14
    
    @staticmethod
    def pack_stock_data(stock_info: dict) -> bytes:
        """재고 정보를 14바이트로 패킹 (AU 명령용)"""
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
    def unpack_response(response: bytes) -> dict:
        """응답을 파싱하여 딕셔너리로 반환"""
        if len(response) < 4:
            return {"error": "응답 길이 부족"}
        
        command = response[:2].decode('ascii').rstrip('\x00')
        status = response[2]
        
        status_map = {
            0x00: "SUCCESS",
            0x01: "FAILURE", 
            0x02: "INVALID_CMD",
            0x03: "INVALID_DATA"
        }
        
        return {
            "command": command,
            "status": status_map.get(status, f"UNKNOWN({status})")
        }
    
    @staticmethod
    def unpack_stock_data(data: bytes) -> dict:
        """14바이트 재고 데이터를 딕셔너리로 변환"""
        if len(data) < 14:
            return {"error": "재고 데이터 길이 부족"}
        
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

"""
if __name__ == "__main__":
    demo = MessageProtocolDemo()
    
    print("=== 메시지 패킹 테스트 ===")
    
    # RI 명령어 테스트
    ri_data = demo.pack_ri_data(5, 3)
    ri_msg = demo.pack_command('RI', ri_data)
    print(f"RI 명령어: {ri_msg.hex()}")
    print(f"길이: {len(ri_msg)}바이트")
    
    # SI 명령어 테스트
    si_data = demo.pack_si_data(2, 4, 1)
    si_msg = demo.pack_command('SI', si_data)
    print(f"SI 명령어: {si_msg.hex()}")
    
    # AU 명령어 테스트
    stock_info = {
        'receiving': 10,
        'red_storage': 15,
        'green_storage': 8,
        'yellow_storage': 12,
        'shipping': 5,
        'receiving_total': 100,
        'shipping_total': 50
    }
    au_data = demo.pack_stock_data(stock_info)
    au_msg = demo.pack_command('AU', au_data)
    print(f"AU 명령어: {au_msg.hex()}")
    
    print("\n=== 응답 파싱 테스트 ===")
    
    # 성공 응답 테스트
    success_response = b'RI\x00\n'  # RI SUCCESS
    parsed = demo.unpack_response(success_response)
    print(f"성공 응답: {parsed}")
    
    # 실패 응답 테스트
    failure_response = b'SI\x01\n'  # SI FAILURE
    parsed = demo.unpack_response(failure_response)
    print(f"실패 응답: {parsed}")
    
    print("\n=== 재고 데이터 언패킹 테스트 ===")
    unpacked_stock = demo.unpack_stock_data(au_data)
    print(f"언패킹된 재고 데이터: {unpacked_stock}")
"""