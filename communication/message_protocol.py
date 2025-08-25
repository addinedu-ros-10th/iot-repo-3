import struct
from typing import Dict, Any

class MessageProtocol:
    """LMS 통신 프로토콜 처리"""
    
    @staticmethod
    def pack_command(command: str, data: bytes) -> bytes:
        """명령어를 17바이트 바이너리로 패킹"""
        cmd_bytes = command.encode('ascii')[:2].ljust(2, b'\x00')
        data_bytes = data[:14].ljust(14, b'\x00')
        end_byte = b'\n'
        return cmd_bytes + data_bytes + end_byte
    
    @staticmethod
    def pack_ri_data(red: int, green: int) -> bytes:
        """RI 명령어 데이터 패킹"""
        return struct.pack('<HH', red, green) + b'\x00' * 10
    
    @staticmethod
    def pack_au_data(stock_info: dict) -> bytes:
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
    def pack_rh_data(success: bool) -> bytes:
        """RH 명령어 데이터 패킹"""
        return struct.pack('<B', 1 if success else 0) + b'\x00' * 13

    @staticmethod
    def pack_si_data(red: int, green: int, yellow: int) -> bytes:
        """SI 명령어 데이터 패킹"""
        return struct.pack('<HHH', red, green, yellow) + b'\x00' * 8    
    
    @staticmethod
    def pack_ra_data() -> bytes:
        """RA 명령어 데이터 패킹"""
        return b'\x00' * 14
    
    @staticmethod
    def unpack_response(response: bytes) -> Dict[str, Any]:
        """응답 파싱"""
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
    def unpack_stock_data(data: bytes) -> Dict[str, Any]:
        """14바이트 재고 데이터 언패킹"""
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