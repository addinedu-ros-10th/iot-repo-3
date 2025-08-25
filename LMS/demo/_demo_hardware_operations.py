"""
LMS 하드웨어 동작 구현 데모
config.py의 Enum과 설정을 활용한 실제 동작 시뮬레이션
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

# config 임포트
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import (
    SectorName, SectorStatus, ItemColor, ColorCode, MotorStatus,
    SECTOR_SENSORS, SECTOR_MOTORS, SECTOR_CAPACITY, COMMANDS
)

class HardwareSimulator:
    """하드웨어 동작 시뮬레이션"""
    
    def __init__(self):
        # 센서 상태
        self.sensor_states = {
            'RGB1': {'color': ItemColor.UNKNOWN, 'active': False},
            'RGB2': {'color': ItemColor.UNKNOWN, 'active': False}, 
            'PROXI1': {'detected': False}
        }
        
        # 모터 상태
        self.motor_states = {
            'SERVO1': MotorStatus.OFF,
            'STEP1': MotorStatus.OFF,
            'DC1': MotorStatus.OFF
        }
        
        print("하드웨어 시뮬레이터 초기화")
    
    def read_rgb_sensor(self, sensor_name: str) -> ItemColor:
        """RGB 센서 읽기"""
        if sensor_name in ['RGB1', 'RGB2']:
            # 시뮬레이션: 랜덤하게 색상 감지
            import random
            colors = [ItemColor.RED, ItemColor.GREEN, ItemColor.YELLOW, ItemColor.UNKNOWN]
            detected_color = random.choice(colors)
            
            self.sensor_states[sensor_name]['color'] = detected_color
            self.sensor_states[sensor_name]['active'] = detected_color != ItemColor.UNKNOWN
            
            print(f"[{sensor_name}] 색상 감지: {detected_color.name}")
            return detected_color
        return ItemColor.UNKNOWN
    
    def read_proximity_sensor(self, sensor_name: str) -> bool:
        """근접 센서 읽기"""
        if sensor_name == 'PROXI1':
            # 시뮬레이션: 50% 확률로 물체 감지
            import random
            detected = random.choice([True, False])
            self.sensor_states[sensor_name]['detected'] = detected
            
            print(f"[{sensor_name}] 물체 감지: {'있음' if detected else '없음'}")
            return detected
        return False
    
    def control_motor(self, motor_name: str, status: MotorStatus, duration: float = 1.0):
        """모터 제어"""
        if motor_name in self.motor_states:
            self.motor_states[motor_name] = status
            
            if status == MotorStatus.ON:
                print(f"[{motor_name}] 모터 ON - {duration}초 동작")
                time.sleep(duration)  # 실제 동작 시간 시뮬레이션
                self.motor_states[motor_name] = MotorStatus.OFF
                print(f"[{motor_name}] 모터 OFF")
            else:
                print(f"[{motor_name}] 모터 OFF")

class SectorManager:
    """구역 관리자"""
    
    def __init__(self, hardware_sim: HardwareSimulator):
        self.hardware = hardware_sim
        
        # 구역 상태
        self.sector_states = {
            SectorName.RECEIVING: SectorStatus.AVAILABLE,
            SectorName.RED_STORAGE: SectorStatus.AVAILABLE,
            SectorName.GREEN_STORAGE: SectorStatus.AVAILABLE,
            SectorName.YELLOW_STORAGE: SectorStatus.AVAILABLE,
            SectorName.SHIPPING: SectorStatus.AVAILABLE
        }
        
        # 구역별 재고
        self.sector_stocks = {
            SectorName.RECEIVING: 0,
            SectorName.RED_STORAGE: 0,
            SectorName.GREEN_STORAGE: 0,
            SectorName.YELLOW_STORAGE: 0,
            SectorName.SHIPPING: 0
        }
        
        print("구역 관리자 초기화")
    
    def process_receiving(self, quantity: int) -> bool:
        """입고 구역 처리"""
        try:
            print(f"\n=== 입고 처리 시작: {quantity}개 ===")
            
            # 1. 입고 구역 상태 확인
            if self.sector_states[SectorName.RECEIVING] != SectorStatus.AVAILABLE:
                print("입고 구역이 사용 불가능합니다")
                return False
            
            # 2. 입고 구역을 처리 중으로 변경
            self.sector_states[SectorName.RECEIVING] = SectorStatus.PROCESSING
            
            # 3. 입고 구역 센서들로 물품 감지
            sensors = SECTOR_SENSORS[SectorName.RECEIVING]
            for sensor in sensors:
                if 'RGB' in sensor:
                    color = self.hardware.read_rgb_sensor(sensor)
                    if color != ItemColor.UNKNOWN:
                        print(f"물품 감지됨: {color.name}")
            
            # 4. 컨베이어 벨트 동작 (DC1)
            motors = SECTOR_MOTORS[SectorName.RECEIVING]
            for motor in motors:
                if motor == 'DC1':  # 컨베이어 벨트
                    self.hardware.control_motor(motor, MotorStatus.ON, 2.0)
                elif motor == 'SERVO1':  # 분류 서보
                    self.hardware.control_motor(motor, MotorStatus.ON, 1.0)
            
            # 5. 재고 업데이트
            self.sector_stocks[SectorName.RECEIVING] += quantity
            
            # 6. 입고 구역 상태 복원
            self.sector_states[SectorName.RECEIVING] = SectorStatus.AVAILABLE
            
            print(f"입고 처리 완료: {quantity}개")
            return True
            
        except Exception as e:
            print(f"입고 처리 실패: {e}")
            self.sector_states[SectorName.RECEIVING] = SectorStatus.UNAVAILABLE
            return False
    
    def process_shipping(self, red: int, green: int, yellow: int) -> bool:
        """출고 구역 처리"""
        try:
            total = red + green + yellow
            print(f"\n=== 출고 처리 시작: R={red}, G={green}, Y={yellow} (총 {total}개) ===")
            
            # 1. 재고 확인
            if (self.sector_stocks[SectorName.RED_STORAGE] < red or
                self.sector_stocks[SectorName.GREEN_STORAGE] < green or
                self.sector_stocks[SectorName.YELLOW_STORAGE] < yellow):
                print("재고 부족으로 출고 불가능")
                return False
            
            # 2. 각 보관구역에서 물품 이동
            if red > 0:
                success = self.move_from_storage(SectorName.RED_STORAGE, red)
                if not success:
                    return False
            
            if green > 0:
                success = self.move_from_storage(SectorName.GREEN_STORAGE, green)
                if not success:
                    return False
            
            if yellow > 0:
                success = self.move_from_storage(SectorName.YELLOW_STORAGE, yellow)
                if not success:
                    return False
            
            # 3. 출고 구역에 물품 집결
            self.sector_stocks[SectorName.SHIPPING] += total
            
            print(f"출고 처리 완료: 총 {total}개")
            return True
            
        except Exception as e:
            print(f"출고 처리 실패: {e}")
            return False
    
    def move_from_storage(self, sector: SectorName, quantity: int) -> bool:
        """보관구역에서 물품 이동"""
        try:
            sector_name = sector.name
            print(f"  {sector_name}에서 {quantity}개 이동 중...")
            
            # 1. 구역 상태 확인
            if self.sector_states[sector] == SectorStatus.UNAVAILABLE:
                print(f"  {sector_name} 구역이 사용 불가능")
                return False
            
            # 2. 구역을 처리 중으로 변경
            self.sector_states[sector] = SectorStatus.PROCESSING
            
            # 3. 근접 센서로 물품 확인
            sensors = SECTOR_SENSORS[sector]
            for sensor in sensors:
                if 'PROXI' in sensor:
                    detected = self.hardware.read_proximity_sensor(sensor)
                    if not detected:
                        print(f"  {sector_name}에 물품이 감지되지 않음")
            
            # 4. 스텝 모터 동작
            motors = SECTOR_MOTORS[sector]
            for motor in motors:
                if 'STEP' in motor:
                    self.hardware.control_motor(motor, MotorStatus.ON, 1.5)
            
            # 5. 재고 감소
            self.sector_stocks[sector] -= quantity
            
            # 6. 구역 상태 복원
            capacity = SECTOR_CAPACITY[sector]
            if capacity > 0 and self.sector_stocks[sector] >= capacity:
                self.sector_states[sector] = SectorStatus.FULL
            else:
                self.sector_states[sector] = SectorStatus.AVAILABLE
            
            print(f"  {sector_name}에서 {quantity}개 이동 완료")
            return True
            
        except Exception as e:
            print(f"  {sector.name} 이동 실패: {e}")
            self.sector_states[sector] = SectorStatus.UNAVAILABLE
            return False
    
    def return_home(self) -> bool:
        """홈 위치로 복귀"""
        try:
            print("\n=== 홈 위치 복귀 시작 ===")
            
            # 모든 모터를 순차적으로 홈 위치로 이동
            all_motors = set()
            for motors in SECTOR_MOTORS.values():
                all_motors.update(motors)
            
            for motor in sorted(all_motors):
                print(f"  {motor} 홈 위치로 이동")
                self.hardware.control_motor(motor, MotorStatus.ON, 0.5)
            
            print("홈 위치 복귀 완료")
            return True
            
        except Exception as e:
            print(f"홈 위치 복귀 실패: {e}")
            return False
    
    def get_status_report(self) -> dict:
        """전체 상태 보고서"""
        return {
            'timestamp': datetime.now(),
            'sector_states': {sector.name: status.name for sector, status in self.sector_states.items()},
            'sector_stocks': {sector.name: stock for sector, stock in self.sector_stocks.items()},
            'sensor_states': self.hardware.sensor_states.copy(),
            'motor_states': {motor: status.name for motor, status in self.hardware.motor_states.items()}
        }

if __name__ == "__main__":
    print("=== LMS 하드웨어 동작 데모 ===")
    
    # 하드웨어 시뮬레이터 생성
    hardware = HardwareSimulator()
    
    # 구역 관리자 생성
    sector_mgr = SectorManager(hardware)
    
    print(f"\n구역별 센서 설정: {dict(SECTOR_SENSORS)}")
    print(f"구역별 모터 설정: {dict(SECTOR_MOTORS)}")
    print(f"구역별 용량 설정: {dict(SECTOR_CAPACITY)}")
    
    # 동작 테스트
    print("\n1. 입고 처리 테스트 (5개)")
    sector_mgr.process_receiving(5)
    
    print("\n2. 출고 처리 테스트 (R=2, G=1, Y=1)")
    sector_mgr.sector_stocks[SectorName.RED_STORAGE] = 3
    sector_mgr.sector_stocks[SectorName.GREEN_STORAGE] = 2
    sector_mgr.sector_stocks[SectorName.YELLOW_STORAGE] = 2
    sector_mgr.process_shipping(2, 1, 1)
    
    print("\n3. 홈 위치 복귀 테스트")
    sector_mgr.return_home()
    
    print("\n4. 전체 상태 보고서")
    status = sector_mgr.get_status_report()
    for key, value in status.items():
        if key != 'timestamp':
            print(f"  {key}: {value}")