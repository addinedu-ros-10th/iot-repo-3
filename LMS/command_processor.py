"""
LMS 명령어 처리기
"""

import struct
import sys
import os
import threading
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import COMMANDS
from communication.message_protocol import MessageProtocol
from stw_lib.sector_manager2 import Robot, RobotStatus, SectorName

class CommandProcessor:
    """명령어 처리기"""
    
    def __init__(self, inventory_manager=None):
        self.inventory_manager = inventory_manager
        
        # 지원 명령어 (지역별 명령어, 초기화 명령어, 로봇 명령어 추가)
        self.supported_commands = ['RI', 'SI', 'RA', 'RH', 'RR', 'RS', 'IR', 'IS', 'IH', 'IA', 'RM']
        
        # Robot 객체 초기화 (LMS에서 로봇 상태 관리)
        self.robot = Robot("LMS_AGV_Robot")
        self.robot_lock = threading.RLock()  # 스레드 안전성
        
        # 위치 매핑 (GUI와 동일)
        self.position_mapping = {
            0: SectorName.RECEIVING,
            1: SectorName.RED_STORAGE,
            2: SectorName.GREEN_STORAGE,
            3: SectorName.YELLOW_STORAGE
        }
        
        print("명령어 처리기 초기화 완료")
        print(f"로봇 초기 위치: {self.robot.location.name}, 상태: {self.robot.status.name}")
    
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
            elif command == 'RR':
                return self.handleRegionalRequest(data, client_id)
            elif command == 'RS':
                return self.handleRegionalStatistics(data, client_id)
            elif command == 'IR':
                return self.handleInitReceive(data, client_id)
            elif command == 'IS':
                return self.handleInitStore(data, client_id)
            elif command == 'IH':
                return self.handleInitShipping(data, client_id)
            elif command == 'IA':
                return self.handleInitAll(data, client_id)
            elif command == 'RM':
                return self.handleRobotMove(data, client_id)
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
            quantity = struct.unpack('<H', data[:2])[0]  # 리틀 엔디안
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
            red_count, green_count, yellow_count = struct.unpack('<HHH', data[:6])  # 리틀 엔디안
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
            print(f"[{client_id}] 전체 재고 요청 (RA → AU + RU)")
            
            if self.inventory_manager:
                extended_data = self.inventory_manager.get_extended_stock_data()
                stock_data = {k: v for k, v in extended_data.items() if k != 'regional_stats'}
                regional_stats = extended_data.get('regional_stats', {})
            else:
                # 가상 데이터
                stock_data = {
                    'receiving': 0, 'red_storage': 10, 'green_storage': 5,
                    'yellow_storage': 8, 'shipping': 2,
                    'receiving_total': 50, 'shipping_total': 30
                }
                regional_stats = {
                    'RED': {'received': 10, 'shipped': 5},
                    'GREEN': {'received': 8, 'shipped': 3},
                    'YELLOW': {'received': 12, 'shipped': 7}
                }
            
            # AU 응답 생성 (GUI_LMS_IO.md 명세에 따라)
            # RECEIVING(2) + RED_STORAGE(2) + GREEN_STORAGE(2) + YELLOW_STORAGE(2) + SHIPPING(2) + RECEIVING누적(2) + SHIPPING누적(2)
            au_data = struct.pack('<HHHHHHH',
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
            
            # RU 응답 생성 (지역별 통계)
            ru_data = MessageProtocol.pack_regional_data(regional_stats)
            ru_message = b'RU' + b'\x00' + ru_data + b'\n'
            
            # AU + RU 결합된 응답
            combined_message = au_message + ru_message
            
            print(f"[{client_id}] AU 응답 생성: ", end = "\n")
            print(f"rec : {stock_data['receiving']}", end=" ")
            print(f"sh : {stock_data['shipping']}", end=" ")
            print(f"r : {stock_data['red_storage']}", end=" ")
            print(f"g : {stock_data['green_storage']}", end=" ")
            print(f"y : {stock_data['yellow_storage']}", end=" ")
            print(f"rect : {stock_data['receiving_total']}", end=" ")
            print(f"sht : {stock_data['shipping_total']}", end="\n")
            
            print(f"[{client_id}] RU 응답 생성: R(받음={regional_stats.get('RED', {}).get('received', 0)},보냄={regional_stats.get('RED', {}).get('shipped', 0)}), "
                  f"G(받음={regional_stats.get('GREEN', {}).get('received', 0)},보냄={regional_stats.get('GREEN', {}).get('shipped', 0)}), "
                  f"Y(받음={regional_stats.get('YELLOW', {}).get('received', 0)},보냄={regional_stats.get('YELLOW', {}).get('shipped', 0)})")

            return combined_message
            
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
    
    def handleRegionalRequest(self, data, client_id):
        """RR 명령: 지역별 재고 요청 처리 → RU 응답"""
        try:
            # 지역 코드 파싱 (1=RED, 2=GREEN, 3=YELLOW, 0=ALL)
            region_code = data[0] if len(data) > 0 else 0
            print(f"[{client_id}] 지역별 재고 요청 (코드: {region_code})")
            
            if self.inventory_manager:
                extended_data = self.inventory_manager.get_extended_stock_data()
                regional_stats = extended_data['regional_stats']
            else:
                # 가상 데이터
                regional_stats = {
                    'RED': {'received': 10, 'shipped': 5},
                    'GREEN': {'received': 8, 'shipped': 3},
                    'YELLOW': {'received': 12, 'shipped': 7}
                }
            
            # RU (Regional Update) 응답 생성
            ru_data = MessageProtocol.pack_regional_data(regional_stats)
            ru_message = b'RU' + b'\x00' + ru_data + b'\n'
            
            print(f"[{client_id}] RU 응답 생성: R(받음={regional_stats['RED']['received']},보냄={regional_stats['RED']['shipped']}), "
                  f"G(받음={regional_stats['GREEN']['received']},보냄={regional_stats['GREEN']['shipped']}), "
                  f"Y(받음={regional_stats['YELLOW']['received']},보냄={regional_stats['YELLOW']['shipped']})")
            
            return ru_message
            
        except Exception as e:
            print(f"[{client_id}] 지역별 재고 요청 처리 오류: {e}")
            return self.createErrorResponse('RR', 0x01)
    
    def handleRegionalStatistics(self, data, client_id):
        """RS 명령: 지역별 통계 요청 처리 → RC 응답"""
        try:
            # 통계 타입 파싱 (0=누적, 1=일별, 2=주별 등)
            stats_type = data[0] if len(data) > 0 else 0
            print(f"[{client_id}] 지역별 통계 요청 (타입: {stats_type})")
            
            if self.inventory_manager:
                regional_stats = self.inventory_manager.get_regional_statistics()
            else:
                # 가상 데이터
                regional_stats = {
                    'RED': {'received': 10, 'shipped': 5},
                    'GREEN': {'received': 8, 'shipped': 3},
                    'YELLOW': {'received': 12, 'shipped': 7}
                }
            
            # RC (Regional Cumulative) 응답 생성
            rc_data = MessageProtocol.pack_regional_data(regional_stats)
            rc_message = b'RC' + b'\x00' + rc_data + b'\n'
            
            print(f"[{client_id}] RC 응답 생성: 지역별 누적 통계")
            
            return rc_message
            
        except Exception as e:
            print(f"[{client_id}] 지역별 통계 요청 처리 오류: {e}")
            return self.createErrorResponse('RS', 0x01)
    
    def handleInitReceive(self, data, client_id):
        """IR 명령: 입고 구역 누적 재고 초기화"""
        try:
            print(f"[{client_id}] : IR 요청")
            
            if self.inventory_manager and hasattr(self.inventory_manager, 'clear_receiving_stock'):
                success = self.inventory_manager.clear_receiving_stock()
                
                if success:
                    print(f"[{client_id}] 입고 구역 초기화 성공")
                    return self.handleRequestAll(data, client_id)  # AU + RU 응답 반환
                else:
                    print(f"[{client_id}] 입고 구역 초기화 실패")
                    return self.createErrorResponse('IR', 0x01)
            else:
                print(f"[{client_id}] 입고 구역 초기화 (시뮬레이션)")
                return self.handleRequestAll(data, client_id)  # AU + RU 응답 반환
                
        except Exception as e:
            print(f"[{client_id}] 입고 구역 초기화 오류: {e}")
            return self.createErrorResponse('IR', 0x01)
    
    def handleInitStore(self, data, client_id):
        """IS 명령: 저장 구역 초기화"""
        try:
            print(f"[{client_id}] 저장 구역 초기화 요청 (IS)")
            
            if self.inventory_manager and hasattr(self.inventory_manager, 'clear_storage_stock'):
                success = self.inventory_manager.clear_storage_stock()
                
                if success:
                    print(f"[{client_id}] 저장 구역 초기화 성공")
                    return self.handleRequestAll(data, client_id)  # AU + RU 응답 반환
                else:
                    print(f"[{client_id}] 저장 구역 초기화 실패")
                    return self.createErrorResponse('IS', 0x01)
            else:
                print(f"[{client_id}] 저장 구역 초기화 (시뮬레이션)")
                return self.handleRequestAll(data, client_id)  # AU + RU 응답 반환
                
        except Exception as e:
            print(f"[{client_id}] 저장 구역 초기화 오류: {e}")
            return self.createErrorResponse('IS', 0x01)
    
    def handleInitShipping(self, data, client_id):
        """IH 명령: 출고 구역 초기화"""
        try:
            print(f"[{client_id}] 출고 구역 초기화 요청 (IH)")
            
            if self.inventory_manager and hasattr(self.inventory_manager, 'clear_shipping_stock'):
                success = self.inventory_manager.clear_shipping_stock()
                
                if success:
                    print(f"[{client_id}] 출고 구역 초기화 성공")
                    return self.handleRequestAll(data, client_id)  # AU + RU 응답 반환
                else:
                    print(f"[{client_id}] 출고 구역 초기화 실패")
                    return self.createErrorResponse('IH', 0x01)
            else:
                print(f"[{client_id}] 출고 구역 초기화 (시뮬레이션)")
                return self.handleRequestAll(data, client_id)  # AU + RU 응답 반환
                
        except Exception as e:
            print(f"[{client_id}] 출고 구역 초기화 오류: {e}")
            return self.createErrorResponse('IH', 0x01)
    
    def handleInitAll(self, data, client_id):
        """IA 명령: 모든 구역 초기화"""
        try:
            print(f"[{client_id}] 모든 구역 초기화 요청 (IA)")
            
            if self.inventory_manager and hasattr(self.inventory_manager, 'clear_all_stock'):
                success = self.inventory_manager.clear_all_stock()
                
                if success:
                    print(f"[{client_id}] 모든 구역 초기화 성공")
                    return self.handleRequestAll(data, client_id)  # AU + RU 응답 반환
                else:
                    print(f"[{client_id}] 모든 구역 초기화 실패")
                    return self.createErrorResponse('IA', 0x01)
            else:
                print(f"[{client_id}] 모든 구역 초기화 (시뮬레이션)")
                return self.handleRequestAll(data, client_id)  # AU + RU 응답 반환
                
        except Exception as e:
            print(f"[{client_id}] 모든 구역 초기화 오류: {e}")
            return self.createErrorResponse('IA', 0x01)
    
    def handleRobotMove(self, data, client_id):
        """RM 명령: 로봇 이동 처리"""
        try:
            # RM 데이터: target_position (1 byte)
            target_position = data[0] if len(data) > 0 else 0
            print(f"[{client_id}] 로봇 이동 명령 - 목표 위치: {target_position}")
            
            with self.robot_lock:
                # 현재 로봇 상태 확인
                if self.robot.status == RobotStatus.MOVING:
                    print(f"[{client_id}] 로봇이 이미 이동 중입니다")
                    return self.createErrorResponse('RM', 0x03)  # BUSY
                
                # 유효한 위치인지 확인
                if target_position not in self.position_mapping:
                    print(f"[{client_id}] 잘못된 위치: {target_position}")
                    return self.createErrorResponse('RM', 0x02)  # INVALID_CMD
                
                target_sector = self.position_mapping[target_position]
                
                # 이미 목표 위치에 있는 경우
                if self.robot.location == target_sector:
                    print(f"[{client_id}] 로봇이 이미 {target_sector.name}에 있습니다")
                    return self.createSuccessResponse('RM')
                
                # 로봇 이동 시작
                print(f"[{client_id}] 로봇 이동 시작: {self.robot.location.name} -> {target_sector.name}")
                success = self._move_robot_to_sector(target_sector, client_id)
                
                if success:
                    print(f"[{client_id}] 로봇 이동 성공: {target_sector.name}")
                    return self.createSuccessResponse('RM')
                else:
                    print(f"[{client_id}] 로봇 이동 실패")
                    return self.createErrorResponse('RM', 0x01)  # FAILURE
                    
        except Exception as e:
            print(f"[{client_id}] 로봇 이동 처리 오류: {e}")
            return self.createErrorResponse('RM', 0x01)
    
    def _move_robot_to_sector(self, target_sector, client_id):
        """로봇을 특정 구역으로 이동시키는 내부 메서드"""
        try:
            # 이동 시작 - 상태를 MOVING으로 변경
            previous_location = self.robot.location
            self.robot.status = RobotStatus.MOVING
            
            print(f"[Robot] 상태 변경: IDLE -> MOVING")
            print(f"[Robot] 이동 경로: {previous_location.name} -> {target_sector.name}")
            
            # 실제 하드웨어 이동 시뮬레이션
            movement_success = self._simulate_robot_movement(previous_location, target_sector)
            
            if movement_success:
                # 이동 성공 - 위치 및 상태 업데이트
                self.robot.location = target_sector
                self.robot.status = RobotStatus.IDLE
                
                print(f"[Robot] 이동 완료: {target_sector.name}")
                print(f"[Robot] 상태 변경: MOVING -> IDLE")
                
                # 도착한 구역에서 필요한 작업 수행
                self._perform_sector_operations(target_sector, client_id)
                
                return True
            else:
                # 이동 실패 - 상태만 원복
                self.robot.status = RobotStatus.IDLE
                print(f"[Robot] 이동 실패 - 상태 복원: MOVING -> IDLE")
                return False
                
        except Exception as e:
            # 예외 발생 시 안전하게 상태 복원
            self.robot.status = RobotStatus.IDLE
            print(f"[Robot] 이동 중 오류 발생: {e}")
            return False
    
    def _simulate_robot_movement(self, from_sector, to_sector):
        """로봇 이동 시뮬레이션 (실제 하드웨어 제어 코드 대체)"""
        try:
            # 이동 시간 계산 (구역간 거리에 따라)
            movement_time = self._calculate_movement_time(from_sector, to_sector)
            
            print(f"[Robot Hardware] 이동 시작: 예상 시간 {movement_time}초")
            
            # 실제 환경에서는 여기에 하드웨어 제어 코드 구현
            # - AGV 모터 제어
            
            # 시뮬레이션용 대기
            time.sleep(movement_time * 0.1)  # 실제 시간의 1/10로 단축
            
            # 이동 성공 확률 (실제로는 센서 피드백 기반)
            movement_success = 1  # 100% 성공률
            
            print(f"[Robot Hardware] 이동 성공")
            return movement_success
            
        except Exception as e:
            print(f"[Robot Hardware] 이동 시뮬레이션 오류: {e}")
            return False
    
    def _calculate_movement_time(self, from_sector, to_sector):
        """구역간 이동 시간 계산"""
        # 실제 환경에서는 물리적 거리와 경로를 기반으로 계산
        base_time = 2.0  # 기본 이동 시간 (초)
        
        # 구역별 거리 매트릭스 (간단한 예시)
        distance_matrix = {
            (SectorName.RECEIVING, SectorName.RED_STORAGE): 2.0,
            (SectorName.RECEIVING, SectorName.GREEN_STORAGE): 2.0,
            (SectorName.RECEIVING, SectorName.YELLOW_STORAGE): 2.0,
            (SectorName.RED_STORAGE, SectorName.GREEN_STORAGE): 2.0,
            (SectorName.RED_STORAGE, SectorName.YELLOW_STORAGE): 2.0,
            (SectorName.GREEN_STORAGE, SectorName.YELLOW_STORAGE): 2.0,
        }
        
        # 양방향 이동
        key1 = (from_sector, to_sector)
        key2 = (to_sector, from_sector)
        
        if key1 in distance_matrix:
            return distance_matrix[key1]
        elif key2 in distance_matrix:
            return distance_matrix[key2]
        else:
            return base_time
    
    def _perform_sector_operations(self, sector, client_id):
        """도착한 구역에서 수행할 작업들"""
        try:
            print(f"[Robot] {sector.name} 구역 도착")
            
            # 구역별 특별한 작업 수행
            if sector == SectorName.RECEIVING:
                print(f"[Robot] 입고 구역 도착 - 물품 수령 가능")
                
            elif sector in [SectorName.RED_STORAGE, SectorName.GREEN_STORAGE, SectorName.YELLOW_STORAGE]:
                print(f"[Robot] {sector.name} 저장 구역 도착 - 물품 보관 가능")
            
            # 작업 상태를 OPERATING으로 변경 (작업이 있는 경우)
            if sector != SectorName.RECEIVING:  # 입고구역 외에는 작업 수행
                self.robot.status = RobotStatus.OPERATING
                print(f"[Robot] 상태 변경: IDLE -> OPERATING")
                
                # 작업 시뮬레이션
                time.sleep(0.5)  # 작업 시간
                
                self.robot.status = RobotStatus.IDLE
                print(f"[Robot] 작업 완료 - 상태 변경: OPERATING -> IDLE")
            
            print(f"[Robot] {sector.name} 구역 작업 완료")
            
        except Exception as e:
            print(f"[Robot] 구역 작업 오류: {e}")
            self.robot.status = RobotStatus.IDLE
    
    def get_robot_status(self):
        """현재 로봇 상태 반환"""
        with self.robot_lock:
            return {
                'name': self.robot.name,
                'status': self.robot.status.name,
                'location': self.robot.location.name,
                'position_code': next((k for k, v in self.position_mapping.items() if v == self.robot.location), -1)
            }
    
    def createSuccessResponse(self, command):
        """성공 응답 생성"""
        return command.encode('ascii').ljust(2, b'\x00') + b'\x00\n'
    
    def createErrorResponse(self, command, error_code):
        """오류 응답 생성"""
        return command.encode('ascii').ljust(2, b'\x00') + bytes([error_code]) + b'\n'