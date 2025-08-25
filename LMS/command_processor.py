"""
LMS 명령어 처리기
"""

import struct
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import COMMANDS
from communication.message_protocol import MessageProtocol

class CommandProcessor:
    """명령어 처리기"""
    
    def __init__(self, inventory_manager=None):
        self.inventory_manager = inventory_manager
        
        # 지원 명령어
        self.supported_commands = ['RI', 'SI', 'RA', 'RH']
        
        print("명령어 처리기 초기화 완료")
    
    def processCommand(self, command, data, client_id):
        """명령어 처리 (메서드명 규칙 적용)"""
        try:
            if command == 'RI':
                return self.handleReceiveItem(data, client_id)
            elif command == 'SI':
                return self.handleShipItem(data, client_id)
            elif command == 'RA':
                return self.handleRequestAll(data, client_id)
            elif command == 'RH':
                return self.handleReturnHome(data, client_id)
            else:
                print(f"지원하지 않는 명령어: {command}")
                return self.createErrorResponse(command, 0x02)  # INVALID_CMD
                
        except Exception as e:
            print(f"명령어 처리 오류: {e}")
            return self.createErrorResponse(command, 0xFF)  # INTERNAL_ERROR
    
    def handleReceiveItem(self, data, client_id):
        """RI 명령: 입고 요청 처리 (GUI_LMS_IO.md 명세 준수)"""
        try:
            # GUI_LMS_IO.md: RI 데이터는 RECEIVE(2 Bytes)
            quantity = struct.unpack('>H', data[:2])[0]  # 빅 엔디안
            print(f"[{client_id}] 입고 요청: {quantity}개")
            
            if self.inventory_manager:
                # 새로운 InventoryManager의 receive_items 메서드 호출
                success = self.inventory_manager.receive_items(quantity)
                
                if success:
                    print(f"[{client_id}] 입고 처리 성공")
                    return self.createSuccessResponse('RI')
                else:
                    print(f"[{client_id}] 입고 처리 실패")
                    return self.createErrorResponse('RI', 0x01)  # FAILURE
            else:
                # 재고 관리자가 없으면 성공으로 처리
                print(f"[{client_id}] 입고 처리 (시뮬레이션)")
                return self.createSuccessResponse('RI')
                
        except Exception as e:
            print(f"[{client_id}] 입고 처리 오류: {e}")
            return self.createErrorResponse('RI', 0x01)
    
    def handleShipItem(self, data, client_id):
        """SI 명령: 출고 요청 처리 (GUI_LMS_IO.md 명세 준수)"""
        try:
            # GUI_LMS_IO.md: SI 데이터는 RED(2) + GREEN(2) + YELLOW(2)
            red_count, green_count, yellow_count = struct.unpack('>HHH', data[:6])  # 빅 엔디안
            print(f"[{client_id}] 출고 요청: RED={red_count}, GREEN={green_count}, YELLOW={yellow_count}")
            
            if self.inventory_manager:
                success = self.inventory_manager.ship_items(red_count, green_count, yellow_count)
                
                if success:
                    print(f"[{client_id}] 출고 처리 성공")
                    return self.createSuccessResponse('SI')
                else:
                    print(f"[{client_id}] 출고 처리 실패")
                    return self.createErrorResponse('SI', 0x01)  # FAILURE
            else:
                print(f"[{client_id}] 출고 처리 (시뮬레이션)")
                return self.createSuccessResponse('SI')
                
        except Exception as e:
            print(f"[{client_id}] 출고 처리 오류: {e}")
            return self.createErrorResponse('SI', 0x01)
    
    def handleRequestAll(self, data, client_id):
        """RA 명령: 전체 재고 요청 처리 → AU 응답"""
        try:
            print(f"[{client_id}] 전체 재고 요청 (RA → AU)")
            
            if self.inventory_manager:
                stock_data = self.inventory_manager.get_current_stock()
            else:
                # 가상 데이터
                stock_data = {
                    'receiving': 0, 'red_storage': 10, 'green_storage': 5,
                    'yellow_storage': 8, 'shipping': 2,
                    'receiving_total': 50, 'shipping_total': 30
                }
            
            # AU 응답 생성 (GUI_LMS_IO.md 명세에 따라)
            # RECEIVING(2) + RED_STORAGE(2) + GREEN_STORAGE(2) + YELLOW_STORAGE(2) + SHIPPING(2) + RECEIVING누적(2) + SHIPPING누적(2)
            au_data = struct.pack('>HHHHHHH',
                stock_data['receiving'],
                stock_data['red_storage'], 
                stock_data['green_storage'],
                stock_data['yellow_storage'],
                stock_data['shipping'],
                stock_data['receiving_total'],
                stock_data['shipping_total']
            )
            
            # AU Command(2) + Status(1) + Data(14) + End(1) = 18 bytes
            au_message = b'AU' + b'\x00' + au_data + b'\n'
            
            print(f"[{client_id}] AU 응답 생성: ", end = "\n")
            print(f"rec : {stock_data['receiving']}", end=" ")
            print(f"sh : {stock_data['shipping']}", end=" ")
            print(f"r : {stock_data['red_storage']}", end=" ")
            print(f"g : {stock_data['green_storage']}", end=" ")
            print(f"y : {stock_data['yellow_storage']}", end=" ")
            print(f"rect : {stock_data['receiving_total']}", end=" ")
            print(f"sht : {stock_data['shipping_total']}", end="\n")

            # print(f"[{client_id}] AU 메시지 hex: {au_message.hex()}")
            return au_message
            
        except Exception as e:
            print(f"[{client_id}] 재고 요청 처리 오류: {e}")
            return self.createErrorResponse('RA', 0x01)
    
    def handleReturnHome(self, data, client_id):
        """RH 명령: 홈 복귀 처리"""
        try:
            # GUI_LMS_IO.md: RH 데이터는 Success(1 Byte)
            success_flag = data[0] if len(data) > 0 else 1
            print(f"[{client_id}] 홈 복귀 명령 (성공 플래그: {success_flag})")
            
            if self.inventory_manager and hasattr(self.inventory_manager, 'return_home'):
                # 실제 홈 복귀 동작 수행
                success = self.inventory_manager.return_home()
                
                if success:
                    print(f"[{client_id}] 홈 복귀 처리 성공")
                    return self.createSuccessResponse('RH')
                else:
                    print(f"[{client_id}] 홈 복귀 처리 실패")
                    return self.createErrorResponse('RH', 0x01)
            else:
                # 시뮬레이션
                print(f"[{client_id}] 홈 복귀 처리 (시뮬레이션)")
                return self.createSuccessResponse('RH')
                
        except Exception as e:
            print(f"[{client_id}] 홈 복귀 처리 오류: {e}")
            return self.createErrorResponse('RH', 0x01)
    
    def createSuccessResponse(self, command):
        """성공 응답 생성"""
        return command.encode('ascii').ljust(2, b'\x00') + b'\x00\n'
    
    def createErrorResponse(self, command, error_code):
        """오류 응답 생성"""
        return command.encode('ascii').ljust(2, b'\x00') + bytes([error_code]) + b'\n'