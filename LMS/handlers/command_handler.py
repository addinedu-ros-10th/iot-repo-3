"""
TCP 명령어 처리 핸들러

TCP 명세서에 따른 모든 명령어를 처리하고 응답을 생성합니다.
"""

import struct
from typing import Tuple, Optional

from ..data.inventory_manager import get_inventory_manager, SectorType


class StatusCode:
    """TCP 명세서 상태 코드"""
    SUCCESS = 0x00
    FAILURE = 0x01
    INVALID_CMD = 0x02
    INVALID_DATA = 0x03


class CommandHandler:
    """TCP 명령어 처리 클래스"""
    
    def __init__(self):
        self.inventory = get_inventory_manager()
        self.command_map = {
            'RS': self.handle_receive_stock,
            'SI': self.handle_shipping_stock,
            'CI': self.handle_color_stock,
            'AI': self.handle_all_stock,
            'CU': self.handle_cumulate_inquiry,
            'RE': self.handle_receive_item,
            'SH': self.handle_ship_item,
            'SO': self.handle_sort_item,
            'CR': self.handle_clear_receiving,
            'CS': self.handle_clear_storage,
            'CH': self.handle_clear_shipping,
            'CA': self.handle_clear_all,
            'RM': self.handle_robot_move,
            'CB': self.handle_conveyor_test,
            'AS': self.handle_agv_servo_test,
            'SM': self.handle_storage_motor_test,
        }
    
    def process_command(self, command: str, data: bytes) -> bytes:
        """
        명령어를 처리하고 응답을 생성합니다.
        
        Args:
            command: 2바이트 명령어 문자열 (예: 'RS', 'AS')
            data: 4바이트 데이터
        
        Returns:
            응답 바이트 (Command + Status + Data + End)
        """
        try:
            if command not in self.command_map:
                return self._create_response(command, StatusCode.INVALID_CMD, b'')
            
            handler = self.command_map[command]
            status, response_data = handler(data)
            
            return self._create_response(command, status, response_data)
            
        except Exception as e:
            print(f"명령어 처리 중 오류 발생: {e}")
            return self._create_response(command, StatusCode.FAILURE, b'')
    
    def _create_response(self, command: str, status: int, data: bytes) -> bytes:
        """응답 패킷을 생성합니다."""
        cmd_bytes = command.encode('ascii')  # 2 bytes
        status_byte = bytes([status])        # 1 byte
        end_byte = b'\n'                    # 1 byte
        
        return cmd_bytes + status_byte + data + end_byte
    
    def handle_receive_stock(self, data: bytes) -> Tuple[int, bytes]:
        """RS - 입고 구역 재고 조회"""
        stock = self.inventory.get_receiving_stock()
        return StatusCode.SUCCESS, struct.pack('>I', stock)
    
    def handle_shipping_stock(self, data: bytes) -> Tuple[int, bytes]:
        """SI - 출고 구역 재고 조회"""
        stock = self.inventory.get_shipping_stock()
        return StatusCode.SUCCESS, struct.pack('>I', stock)
    
    def handle_color_stock(self, data: bytes) -> Tuple[int, bytes]:
        """CI - 특정 색상 저장 구역 재고 조회"""
        if len(data) < 1:
            return StatusCode.INVALID_DATA, b''
        
        color_code = data[0]
        stock = self.inventory.get_color_storage_stock(color_code)
        
        if stock is None:
            return StatusCode.INVALID_DATA, b''
        
        return StatusCode.SUCCESS, struct.pack('>I', stock)
    
    def handle_all_stock(self, data: bytes) -> Tuple[int, bytes]:
        """AI - 모든 구역 재고 조회"""
        all_stock = self.inventory.get_all_stock()
        
        # TCP 명세서 순서에 맞춰 20바이트 데이터 생성
        stock_data = struct.pack('>IIIII',
            all_stock[SectorType.RECEIVING],
            all_stock[SectorType.RED_STORAGE],
            all_stock[SectorType.GREEN_STORAGE],
            all_stock[SectorType.YELLOW_STORAGE],
            all_stock[SectorType.SHIPPING]
        )
        
        return StatusCode.SUCCESS, stock_data
    
    def handle_cumulate_inquiry(self, data: bytes) -> Tuple[int, bytes]:
        """CU - 누적 입출고 재고 조회"""
        cumulative_stock = self.inventory.get_cumulative_stock()
        
        # TCP 명세서에 따라 8바이트 데이터 생성 (RECEIVING, SHIPPING 순서)
        cumulative_data = struct.pack('>II',
            cumulative_stock[SectorType.RECEIVING],
            cumulative_stock[SectorType.SHIPPING]
        )
        
        return StatusCode.SUCCESS, cumulative_data
    
    def handle_receive_item(self, data: bytes) -> Tuple[int, bytes]:
        """RE - 입고 구역으로 물품 입고"""
        if len(data) < 4:
            return StatusCode.INVALID_DATA, b''
        
        quantity = struct.unpack('>I', data[:4])[0]
        
        if quantity <= 0:
            return StatusCode.INVALID_DATA, b''
        
        success, new_stock = self.inventory.receive_items(quantity)
        
        if success:
            return StatusCode.SUCCESS, struct.pack('>I', new_stock)
        else:
            return StatusCode.FAILURE, struct.pack('>I', new_stock)
    
    def handle_ship_item(self, data: bytes) -> Tuple[int, bytes]:
        """SH - 특정 색상 저장 구역에서 출고 구역으로 물품 이동"""
        if len(data) < 1:
            return StatusCode.INVALID_DATA, b''
        
        color_code = data[0]
        success = self.inventory.ship_item(color_code)
        
        if success:
            return StatusCode.SUCCESS, b''
        else:
            return StatusCode.FAILURE, b''
    
    def handle_sort_item(self, data: bytes) -> Tuple[int, bytes]:
        """SO - 입고 구역에서 특정 색상 저장 구역으로 물품 이동"""
        if len(data) < 1:
            return StatusCode.INVALID_DATA, b''
        
        color_code = data[0]
        success = self.inventory.sort_item(color_code)
        
        if success:
            return StatusCode.SUCCESS, b''
        else:
            return StatusCode.FAILURE, b''
    
    def handle_clear_receiving(self, data: bytes) -> Tuple[int, bytes]:
        """CR - 입고 구역 재고 초기화"""
        try:
            self.inventory.reset_receiving_stock()
            return StatusCode.SUCCESS, b''
        except Exception:
            return StatusCode.FAILURE, b''
    
    def handle_clear_storage(self, data: bytes) -> Tuple[int, bytes]:
        """CS - 보관 구역 재고 초기화 (R, G, Y)"""
        try:
            self.inventory.reset_storage_stock()
            return StatusCode.SUCCESS, b''
        except Exception:
            return StatusCode.FAILURE, b''
    
    def handle_clear_shipping(self, data: bytes) -> Tuple[int, bytes]:
        """CH - 출고 구역 재고 초기화"""
        try:
            self.inventory.reset_shipping_stock()
            return StatusCode.SUCCESS, b''
        except Exception:
            return StatusCode.FAILURE, b''
    
    def handle_clear_all(self, data: bytes) -> Tuple[int, bytes]:
        """CA - 전체 구역 재고 초기화"""
        try:
            self.inventory.reset_all_stock()
            return StatusCode.SUCCESS, b''
        except Exception:
            return StatusCode.FAILURE, b''
    
    def handle_robot_move(self, data: bytes) -> Tuple[int, bytes]:
        """RM - 로봇 이동 명령"""
        if len(data) < 1:
            return StatusCode.INVALID_DATA, b''
        
        position = data[0]  # 0: 입고, 1: R, 2: G, 3: Y, 4: 출고
        
        if position > 4:
            return StatusCode.INVALID_DATA, b''
        
        try:
            # 실제 로봇 제어 로직은 여기에 구현
            # 현재는 시뮬레이션으로 항상 성공 반환
            print(f"로봇 이동 명령: 위치 {position}")
            return StatusCode.SUCCESS, b''
        except Exception:
            return StatusCode.FAILURE, b''
    
    def handle_conveyor_test(self, data: bytes) -> Tuple[int, bytes]:
        """CB - 컨베이어 벨트 테스트"""
        try:
            # 실제 컨베이어 벨트 제어 로직은 여기에 구현
            print("컨베이어 벨트 테스트 실행")
            return StatusCode.SUCCESS, b''
        except Exception:
            return StatusCode.FAILURE, b''
    
    def handle_agv_servo_test(self, data: bytes) -> Tuple[int, bytes]:
        """AS - AGV 서보모터 테스트"""
        try:
            # 실제 AGV 서보모터 제어 로직은 여기에 구현
            print("AGV 서보모터 테스트 실행")
            return StatusCode.SUCCESS, b''
        except Exception:
            return StatusCode.FAILURE, b''
    
    def handle_storage_motor_test(self, data: bytes) -> Tuple[int, bytes]:
        """SM - 보관함 서보모터 테스트"""
        if len(data) < 1:
            return StatusCode.INVALID_DATA, b''
        
        color_code = data[0]  # 0x01: R, 0x02: G, 0x03: Y
        
        if color_code not in [0x01, 0x02, 0x03]:
            return StatusCode.INVALID_DATA, b''
        
        try:
            # 실제 보관함 서보모터 제어 로직은 여기에 구현
            color_names = {0x01: 'R', 0x02: 'G', 0x03: 'Y'}
            print(f"보관함 {color_names[color_code]} 구역 서보모터 테스트 실행")
            return StatusCode.SUCCESS, b''
        except Exception:
            return StatusCode.FAILURE, b''


def create_command_handler() -> CommandHandler:
    """명령어 핸들러 인스턴스 생성"""
    return CommandHandler()