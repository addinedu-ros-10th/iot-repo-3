"""
LMS 재고 관리자 - config.py 기반 실제 동작 구현
하드웨어 시뮬레이션과 센서/모터 제어 포함
"""

import threading
import time
import sys
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

# config 임포트
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import (
    SectorName, SectorStatus, ItemColor, MotorStatus,
    SECTOR_CAPACITY, SECTOR_SENSORS, SECTOR_MOTORS, COMMANDS
)

class HardwareSimulator:
    """하드웨어 동작 시뮬레이터"""
    
    def __init__(self):
        # 센서 상태
        self.sensor_states = {
            'RGB1': {'color': ItemColor.UNKNOWN, 'active': False},
            'RGB2': {'color': ItemColor.UNKNOWN, 'active': False}, 
            'PROXI1': {'detected': False, 'count': 0}
        }
        
        # 모터 상태
        self.motor_states = {
            'SERVO1': MotorStatus.OFF,
            'STEP1': MotorStatus.OFF,
            'DC1': MotorStatus.OFF
        }
    
    def read_rgb_sensor(self, sensor_name: str, simulate_color: ItemColor = None) -> ItemColor:
        """RGB 센서 색상 감지"""
        if sensor_name in self.sensor_states:
            if simulate_color:
                color = simulate_color
            else:
                # 시뮬레이션: 입고 시에는 다양한 색상, 평상시에는 UNKNOWN
                import random
                colors = [ItemColor.RED, ItemColor.GREEN, ItemColor.YELLOW]
                color = random.choice(colors)
            
            self.sensor_states[sensor_name]['color'] = color
            self.sensor_states[sensor_name]['active'] = True
            print(f"[{sensor_name}] 색상 감지: {color.name}")
            return color
        return ItemColor.UNKNOWN
    
    def read_proximity_sensor(self, sensor_name: str) -> int:
        """근접 센서 물품 개수 감지"""
        if sensor_name == 'PROXI1':
            # 시뮬레이션: 현재 저장된 개수 반환
            count = self.sensor_states[sensor_name]['count']
            detected = count > 0
            self.sensor_states[sensor_name]['detected'] = detected
            print(f"[{sensor_name}] 물품 개수: {count}개")
            return count
        return 0
    
    def control_motor(self, motor_name: str, duration: float = 1.0) -> bool:
        """모터 동작 제어"""
        if motor_name in self.motor_states:
            self.motor_states[motor_name] = MotorStatus.ON
            print(f"[{motor_name}] 모터 동작 시작 ({duration}초)")
            
            # 실제 환경에서는 하드웨어 제어 코드
            time.sleep(duration * 0.1)  # 시뮬레이션용 단축
            
            self.motor_states[motor_name] = MotorStatus.OFF
            print(f"[{motor_name}] 모터 동작 완료")
            return True
        return False
    
    def update_sensor_count(self, sensor_name: str, count: int):
        """센서 감지 개수 업데이트 (시뮬레이션용)"""
        if sensor_name in self.sensor_states:
            self.sensor_states[sensor_name]['count'] = count

class InventoryManager:
    """config.py 기반 고도화된 재고 관리자"""
    
    def __init__(self):
        # 하드웨어 시뮬레이터
        self.hardware = HardwareSimulator()
        
        # Enum 기반 구역별 재고
        self.sector_stocks = {
            SectorName.RECEIVING: 0,
            SectorName.RED_STORAGE: 0,
            SectorName.GREEN_STORAGE: 0,
            SectorName.YELLOW_STORAGE: 0,
            SectorName.SHIPPING: 0
        }
        
        # 구역별 상태
        self.sector_states = {
            SectorName.RECEIVING: SectorStatus.AVAILABLE,
            SectorName.RED_STORAGE: SectorStatus.AVAILABLE,
            SectorName.GREEN_STORAGE: SectorStatus.AVAILABLE,
            SectorName.YELLOW_STORAGE: SectorStatus.AVAILABLE,
            SectorName.SHIPPING: SectorStatus.AVAILABLE
        }
        
        # 누적 통계
        self.cumulative_stats = {
            'total_received': 0,
            'total_shipped': 0,
            'operations_log': []
        }
        
        # 지역별 누적 통계 (main_monitor.ui 우측 상단 지역 색상별 입고/출고 현황)
        self.regional_cumulative_stats = {
            ItemColor.RED: {'received': 0, 'shipped': 0},
            ItemColor.GREEN: {'received': 0, 'shipped': 0},
            ItemColor.YELLOW: {'received': 0, 'shipped': 0}
        }
        
        # 스레드 안전성
        self.lock = threading.RLock()
        
        self.log_operation("시스템 초기화", "재고 관리자 시작")
    
    def get_current_stock(self):
        """현재 재고 현황 반환 (AU 명령 응답 형식)"""
        with self.lock:
            return {
                'receiving': self.sector_stocks[SectorName.RECEIVING],
                'red_storage': self.sector_stocks[SectorName.RED_STORAGE],
                'green_storage': self.sector_stocks[SectorName.GREEN_STORAGE],
                'yellow_storage': self.sector_stocks[SectorName.YELLOW_STORAGE],
                'shipping': self.sector_stocks[SectorName.SHIPPING],
                'receiving_total': self.cumulative_stats['total_received'],
                'shipping_total': self.cumulative_stats['total_shipped']
            }
    
    def log_operation(self, operation: str, details: str):
        """작업 로그 기록"""
        log_entry = {
            'timestamp': datetime.now(),
            'operation': operation,
            'details': details
        }
        self.cumulative_stats['operations_log'].append(log_entry)
        
        # 로그 크기 제한 (최근 100개만 유지)
        if len(self.cumulative_stats['operations_log']) > 100:
            self.cumulative_stats['operations_log'] = self.cumulative_stats['operations_log'][-100:]
    
    def receive_items(self, quantity: int) -> bool:
        """RI 명령: 실제 하드웨어 기반 입고 처리"""
        with self.lock:
            try:
                print(f"\n=== 입고 처리 시작: {quantity}개 ===")
                self.log_operation("입고 시작", f"요청 수량: {quantity}개")
                
                # 1. 입고구역 상태 확인
                if self.sector_states[SectorName.RECEIVING] != SectorStatus.AVAILABLE:
                    print("입고구역이 사용 불가능합니다")
                    return False
                
                # 2. 입고구역을 처리 중으로 변경
                self.sector_states[SectorName.RECEIVING] = SectorStatus.PROCESSING
                
                # 3. 컨베이어 벨트와 센서 동작
                success = self._process_receiving_hardware(quantity)
                if not success:
                    self.sector_states[SectorName.RECEIVING] = SectorStatus.AVAILABLE
                    return False
                
                # 4. 색상별 분류 및 저장
                colors_received = self._classify_and_store(quantity)
                
                # 5. 누적 통계만 업데이트 (재고는 _classify_and_store에서 이미 처리됨)
                self.cumulative_stats['total_received'] += quantity
                
                # 6. 입고구역 상태 복원
                self.sector_states[SectorName.RECEIVING] = SectorStatus.AVAILABLE
                
                details = f"완료 - " + ", ".join([f"{color.name}={count}" for color, count in colors_received.items()])
                self.log_operation("입고 완료", details)
                print(f"입고 처리 완료: {quantity}개")
                return True
                
            except Exception as e:
                print(f"입고 처리 실패: {e}")
                self.sector_states[SectorName.RECEIVING] = SectorStatus.UNAVAILABLE
                self.log_operation("입고 실패", str(e))
                return False
    
    def _process_receiving_hardware(self, quantity: int) -> bool:
        """입고구역 하드웨어 동작"""
        try:
            # RECEIVING 구역 모터들 동작
            motors = SECTOR_MOTORS[SectorName.RECEIVING]
            
            # DC1 (컨베이어 벨트) 동작
            if 'DC1' in motors:
                print("컨베이어 벨트 동작 중...")
                self.hardware.control_motor('DC1', 2.0)
            
            # SERVO1 (분류기) 동작  
            if 'SERVO1' in motors:
                print("분류 서보모터 동작 중...")
                self.hardware.control_motor('SERVO1', 1.5)
            
            return True
            
        except Exception as e:
            print(f"입고구역 하드웨어 오류: {e}")
            return False
    
    def _classify_and_store(self, quantity: int) -> Dict[ItemColor, int]:
        """색상 분류 및 저장구역 이동"""
        colors_received = {ItemColor.RED: 0, ItemColor.GREEN: 0, ItemColor.YELLOW: 0}
        
        try:
            # RGB 센서로 색상 감지 (시뮬레이션)
            sensors = SECTOR_SENSORS[SectorName.RECEIVING]
            
            for i in range(quantity):
                # RGB1 센서로 색상 감지
                if 'RGB1' in sensors:
                    detected_color = self.hardware.read_rgb_sensor('RGB1')
                    colors_received[detected_color] += 1
                    
                    # 해당 색상 보관구역에 저장
                    if detected_color == ItemColor.RED:
                        self._store_to_sector(SectorName.RED_STORAGE, 1)
                    elif detected_color == ItemColor.GREEN:
                        self._store_to_sector(SectorName.GREEN_STORAGE, 1)
                    elif detected_color == ItemColor.YELLOW:
                        self._store_to_sector(SectorName.YELLOW_STORAGE, 1)
                    else:
                        # UNKNOWN 색상은 RECEIVING 구역에 남김 (분류 실패)
                        print(f"분류 실패: UNKNOWN 색상을 RECEIVING 구역에 보관")
                        self.sector_stocks[SectorName.RECEIVING] += 1
            
            return colors_received
            
        except Exception as e:
            print(f"색상 분류 실패: {e}")
            return colors_received
    
    def _store_to_sector(self, sector: SectorName, quantity: int):
        """특정 보관구역에 저장"""
        try:
            # 용량 확인
            capacity = SECTOR_CAPACITY[sector]
            current_stock = self.sector_stocks[sector]
            
            if capacity > 0 and current_stock + quantity > capacity:
                print(f"{sector.name} 구역 용량 초과")
                self.sector_states[sector] = SectorStatus.FULL
                return False
            
            # 재고 증가
            self.sector_stocks[sector] += quantity
            
            # 하드웨어 센서 카운트 업데이트
            sensors = SECTOR_SENSORS[sector]
            for sensor in sensors:
                if 'PROXI' in sensor:
                    self.hardware.update_sensor_count(sensor, self.sector_stocks[sector])
            
            print(f"{sector.name}에 {quantity}개 저장 (총 {self.sector_stocks[sector]}개)")
            return True
            
        except Exception as e:
            print(f"{sector.name} 저장 실패: {e}")
            return False
    
    def ship_items(self, red_count: int, green_count: int, yellow_count: int) -> bool:
        """SI 명령: 실제 하드웨어 기반 출고 처리"""
        with self.lock:
            try:
                total = red_count + green_count + yellow_count
                print(f"\n=== 출고 처리 시작: R={red_count}, G={green_count}, Y={yellow_count} (총 {total}개) ===")
                self.log_operation("출고 시작", f"R={red_count}, G={green_count}, Y={yellow_count}")
                
                # 1. 재고 확인
                if not self._check_stock_availability(red_count, green_count, yellow_count):
                    print("재고 부족으로 출고 불가")
                    return False
                
                # 2. 각 보관구역에서 출고
                success = True
                if red_count > 0:
                    success &= self._ship_from_sector(SectorName.RED_STORAGE, red_count)
                if green_count > 0:
                    success &= self._ship_from_sector(SectorName.GREEN_STORAGE, green_count)
                if yellow_count > 0:
                    success &= self._ship_from_sector(SectorName.YELLOW_STORAGE, yellow_count)
                
                if not success:
                    print("출고 처리 중 오류 발생")
                    return False
                
                # 3. 출고구역에 집결
                self.sector_stocks[SectorName.SHIPPING] += total
                self.cumulative_stats['total_shipped'] += total
                
                self.log_operation("출고 완료", f"총 {total}개 출고")
                print(f"출고 처리 완료: 총 {total}개")
                return True
                
            except Exception as e:
                print(f"출고 처리 실패: {e}")
                self.log_operation("출고 실패", str(e))
                return False
    
    def _check_stock_availability(self, red: int, green: int, yellow: int) -> bool:
        """재고 가용성 확인"""
        print(f"재고 확인:")
        print(f"  요청: R={red}, G={green}, Y={yellow}")
        print(f"  현재 재고: R={self.sector_stocks[SectorName.RED_STORAGE]}, G={self.sector_stocks[SectorName.GREEN_STORAGE]}, Y={self.sector_stocks[SectorName.YELLOW_STORAGE]}")
        
        available = (self.sector_stocks[SectorName.RED_STORAGE] >= red and
                    self.sector_stocks[SectorName.GREEN_STORAGE] >= green and
                    self.sector_stocks[SectorName.YELLOW_STORAGE] >= yellow)
        
        print(f"  재고 충분: {available}")
        return available
    
    def _ship_from_sector(self, sector: SectorName, quantity: int) -> bool:
        """특정 보관구역에서 출고"""
        try:
            print(f"  {sector.name}에서 {quantity}개 출고 중...")
            
            # 1. 구역 상태를 처리 중으로 변경
            self.sector_states[sector] = SectorStatus.PROCESSING
            
            # 2. 근접 센서로 재고 확인
            sensors = SECTOR_SENSORS[sector]
            for sensor in sensors:
                if 'PROXI' in sensor:
                    current_count = self.hardware.read_proximity_sensor(sensor)
                    if current_count < quantity:
                        print(f"  {sector.name} 센서 감지 재고 부족: {current_count}개 < {quantity}개")
            
            # 3. 스텝모터 동작 (보관구역 출고)
            motors = SECTOR_MOTORS[sector]
            for motor in motors:
                if 'STEP' in motor:
                    self.hardware.control_motor(motor, 1.5)
            
            # 4. 재고 차감
            self.sector_stocks[sector] -= quantity
            
            # 5. 센서 카운트 업데이트
            for sensor in sensors:
                if 'PROXI' in sensor:
                    self.hardware.update_sensor_count(sensor, self.sector_stocks[sector])
            
            # 6. 구역 상태 복원
            self.sector_states[sector] = SectorStatus.AVAILABLE
            
            print(f"  {sector.name}에서 {quantity}개 출고 완료 (잔여: {self.sector_stocks[sector]}개)")
            return True
            
        except Exception as e:
            print(f"  {sector.name} 출고 실패: {e}")
            self.sector_states[sector] = SectorStatus.UNAVAILABLE
            return False
    
    def return_home(self) -> bool:
        """RH 명령: 모든 모터를 홈 위치로 복귀"""
        with self.lock:
            try:
                print("\n=== 홈 위치 복귀 시작 ===")
                self.log_operation("홈 복귀 시작", "모든 모터 홈 위치 이동")
                
                # 모든 모터를 홈 위치로 이동
                all_motors = set()
                for motors in SECTOR_MOTORS.values():
                    all_motors.update(motors)
                
                for motor in sorted(all_motors):
                    print(f"  {motor} 홈 위치로 이동")
                    success = self.hardware.control_motor(motor, 0.5)
                    if not success:
                        print(f"  {motor} 홈 복귀 실패")
                        return False
                
                self.log_operation("홈 복귀 완료", f"{len(all_motors)}개 모터 홈 복귀")
                print("홈 위치 복귀 완료")
                return True
                
            except Exception as e:
                print(f"홈 위치 복귀 실패: {e}")
                self.log_operation("홈 복귀 실패", str(e))
                return False