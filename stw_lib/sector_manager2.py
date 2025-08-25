from enum import Enum, auto
from typing import List, Dict, Optional

# --- 상수 정의 (Enums) ---

class SectorName(Enum):
  """각 구역의 고유한 이름을 정의합니다."""
  RECEIVING = auto()        # 입고 전 물품, 색을 알 수 없는 물품 저장 (ItemColor : UNKNOWN)
  RED_STORAGE = auto()      # 입고 후 빨간색 물품 저장 구역 (ItemColor : RED)
  GREEN_STORAGE = auto()    # 입고 후 초록색 물품 저장 구역 (ItemColor : GREEN)
  YELLOW_STORAGE = auto()   # 입고 후 노란색 물품 저장 구역 (ItemColor : YELLOW)
  SHIPPING = auto()         # 출고 후 3색 물품 처리 구역   (ItemColor : R / G / Y)

class ItemColor(Enum):
  """물품의 종류를 나타내는 색상을 정의합니다."""
  UNKNOWN = auto()  # 입고 전 / 분류 실패
  RED = auto()
  GREEN = auto()
  YELLOW = auto()

class SectorStatus(Enum):
  """구역의 상태를 정의합니다."""
  AVAILABLE = auto()    # 사용 가능 (비어 있음)
  PROCESSING = auto()   # 사용 중 (물품 처리 중)
  UNAVAILABLE = auto()  # 사용 불가능 (오류 등)
  FULL = auto()         # 가득 참

class MotorStatus(Enum):
  """모터의 상태를 정의합니다."""
  ON = auto()
  OFF = auto()

class RobotStatus(Enum):
    IDLE = auto()
    MOVING = auto()
    OPERATING = auto()  # 물품 수령/전달 등

class Robot:
  def __init__(self, name):
    self.name = name
    self.status = RobotStatus.IDLE # 로봇 쉬는중
    self.location = SectorName.RECEIVING # 초기 위치 : 입고구역

  def move_to_sector(self, new_sector):
    if self.location == new_sector:
      print(f"[{self.name}] 이미 {new_sector.name} 구역에 있습니다.")
      return

    # (추가) 용량 체크 로직
    # 현재 구역에서 로봇 수 감소, 새 구역에서 로봇 수 증가
    
    print(f"[{self.name}] {self.location.name} -> {new_sector.name} 으로 이동 시작")
    self.operation_status = RobotStatus.MOVING
    
    # 실제 이동 시간/로직 시뮬레이션
    # ...
    
    print(f"[{self.name}] {new_sector.name} 구역에 도착했습니다.")
    self.location = new_sector
    self.operation_status = RobotStatus.IDLE

  def get_info(self):
    print(f"--- 로봇 [{self.name}] 상태 정보 ---")
    print(f"  - 현재 동작 상태: {self.operation_status.name}")
    print(f"  - 현재 위치 구역: {self.location.name}")
    print("-" * 25)

class Motor:
  """
  하나의 모터를 나타내는 클래스.
  이름과 상태(ON/OFF) 정보를 가집니다.
  """
  def __init__(self, name: str):
    self.name = name
    self.status: MotorStatus = MotorStatus.OFF # 모든 모터는 OFF 상태에서 시작

  def turn_on(self):
    if self.status != MotorStatus.ON:
      print(f"  - 모터 [{self.name}] 상태 변경: OFF -> ON")
      self.status = MotorStatus.ON

  def turn_off(self):
    if self.status != MotorStatus.OFF:
      print(f"  - 모터 [{self.name}] 상태 변경: ON -> OFF")
      self.status = MotorStatus.OFF
  
  def __repr__(self):
    return f"Motor(name={self.name}, status={self.status.name})"



'''
# class Robot 구현
- 멤버변수
  - self.stock : (로봇은 한번에 하나의 물품만 옮길 수 있음) 0 : 물품 없음 / 1 : 물품 분류작업 중
  - self.location : 
'''

# --- Sector 클래스 ---

class Sector:
  """
  하나의 구역(Sector)을 나타내는 클래스.
  상태, 재고, 용량 정보를 포함하고 관련 메서드를 제공합니다.
  """
  def __init__(self, name: SectorName, capacity: int = 0, sensor_list: Optional[List[str]] = None, motor_list: Optional[List[str]] = None):
    self.name = name
    self.capacity = capacity
    self.stock: int = 0
    self.sensor_list: List[str] = sensor_list if sensor_list is not None else []
    
    # motor_list를 Motor 객체의 딕셔너리로 변환하여 저장
    self.motors: Dict[str, Motor] = {motor_name: Motor(motor_name) for motor_name in motor_list} if motor_list else {}
    self.status: SectorStatus = SectorStatus.UNAVAILABLE

  # --- 모터 제어 관련 메서드 ---
  def turn_on_motor(self, motor_name: str) -> bool:
    """지정된 이름의 모터를 켭니다."""
    if motor_name in self.motors:
      self.motors[motor_name].turn_on()
      return True
    print(f"오류: [{self.name.name}] 구역에 '{motor_name}' 모터가 존재하지 않습니다.")
    return False

  def turn_off_motor(self, motor_name: str) -> bool:
    """지정된 이름의 모터를 끕니다."""
    if motor_name in self.motors:
      self.motors[motor_name].turn_off()
      return True
    print(f"오류: [{self.name.name}] 구역에 '{motor_name}' 모터가 존재하지 않습니다.")
    return False
    
  def get_motor_status(self, motor_name: str) -> Optional[MotorStatus]:
    """지정된 이름의 모터 상태를 반환합니다."""
    if motor_name in self.motors:
      return self.motors[motor_name].status
    print(f"오류: [{self.name.name}] 구역에 '{motor_name}' 모터가 존재하지 않습니다.")
    return None

  def display_motor_statuses(self):
    """해당 구역의 모든 모터 상태를 출력합니다."""
    print(f"--- [{self.name.name}] 구역 모터 상태 ---")
    if not self.motors:
      print("  (모터 없음)")
    else:
      for motor_name, motor in self.motors.items():
        print(f"  - {motor_name:<8}: {motor.status.name}")
    print("--------------------------")


  # ------------------------------------------
  
  def update_status(self, new_status: SectorStatus):
    if self.status != new_status:
      print(f"[{self.name.name}] 상태 변경: {self.status.name} -> {new_status.name}")
      self.status = new_status

  def add_stock(self, quantity: int = 1) -> bool:
    if self.capacity != 0 and self.stock + quantity > self.capacity:
      print(f"[{self.name.name}] 재고 추가 실패: 용량 초과 (현재: {self.stock}, 용량: {self.capacity})")
      return False
    
    self.stock += quantity
    print(f"[{self.name.name}] 재고 추가: {self.stock - quantity} -> {self.stock}")
    
    if self.capacity != 0 and self.stock == self.capacity:
      self.update_status(SectorStatus.FULL)
    elif self.status == SectorStatus.AVAILABLE: # 비어있다가 재고가 생기면 PROCESSING으로
        self.update_status(SectorStatus.PROCESSING)
    return True

  def remove_stock(self, quantity: int = 1) -> bool:
    if self.stock - quantity < 0:
      print(f"[{self.name.name}] 재고 제거 실패: 재고 부족 (현재: {self.stock})")
      return False
      
    self.stock -= quantity
    print(f"[{self.name.name}] 재고 제거: {self.stock + quantity} -> {self.stock}")
    
    if self.stock == 0:
      self.update_status(SectorStatus.AVAILABLE)
    # 꽉 차있다가 재고가 빠지면 PROCESSING으로
    elif self.status == SectorStatus.FULL and self.stock < self.capacity:
      self.update_status(SectorStatus.PROCESSING)
    return True

  @property
  def is_available_for_storage(self) -> bool:
    """새로운 물품을 보관할 수 있는 상태인지 확인 (용량 체크)"""
    if self.status == SectorStatus.FULL:
        return False
    if self.capacity == 0: # 무제한 용량
        return True
    return self.stock < self.capacity

  def __repr__(self):
    capacity_str = "무제한" if self.capacity == 0 else str(self.capacity)
    return (f"Sector(name={self.name.name}, status={self.status.name}, "
            f"stock={self.stock}/{capacity_str})")

# --- SectorManager 클래스 ---

class SectorManager:
  """
  전체 구역을 중앙에서 관리하는 싱글톤 클래스.
  """
  _instance = None

  def __new__(cls, *args, **kwargs):
    if not cls._instance:
      cls._instance = super(SectorManager, cls).__new__(cls, *args, **kwargs)
    return cls._instance

  def __init__(self):
    if not hasattr(self, 'initialized'):
      self.sectors: Dict[SectorName, Sector] = {
        # 입고 구역 : 로봇
        SectorName.RECEIVING: Sector(name=SectorName.RECEIVING, capacity=0, sensor_list=["RGB1", "RGB2"], motor_list=["SERVO1", "STEP1", "DC1"]),
        SectorName.RED_STORAGE: Sector(name=SectorName.RED_STORAGE, capacity=3, sensor_list=["PROXI1"], motor_list=["STEP1"]),
        SectorName.GREEN_STORAGE: Sector(name=SectorName.GREEN_STORAGE, capacity=3, sensor_list=["PROXI1"], motor_list=["STEP1"]),
        SectorName.YELLOW_STORAGE: Sector(name=SectorName.YELLOW_STORAGE, capacity=3, sensor_list=["PROXI1"], motor_list=["STEP1"]),
        SectorName.SHIPPING: Sector(name=SectorName.SHIPPING, capacity=0, sensor_list=["RGB1"])
      }
      self.initialized = True

  def update_sector_status(self, name: SectorName, new_status: SectorStatus) -> bool:
    """
    특정 구역의 상태를 직접 업데이트합니다.

    Args:
        name (SectorName): 상태를 변경할 구역의 이름.
        new_status (SectorStatus): 설정할 새로운 상태.

    Returns:
        bool: 상태 변경 성공 시 True, 해당 구역이 존재하지 않으면 False.
    """
    if name in self.sectors:
      sector_to_update = self.get_sector(name)
      sector_to_update.update_status(new_status)
      return True
    else:
      print(f"오류: '{name}'에 해당하는 구역을 찾을 수 없습니다.")
      return False

  def initialize_all_sectors(self):
    print("--- 모든 구역을 사용 가능(AVAILABLE) 상태로 초기화합니다. ---")
    for sector in self.sectors.values():
      sector.update_status(SectorStatus.AVAILABLE)

  def get_sector(self, name: SectorName) -> Sector:
    return self.sectors[name]

  def _get_storage_sector_name(self, color: ItemColor) -> Optional[SectorName]:
    if color == ItemColor.UNKNOWN:
        return None
    return SectorName[f"{color.name}_STORAGE"]

  def receive_new_item(self) -> bool:
    """새로운 (UNKNOWN) 물품을 입고 구역(RECEIVING)에 추가합니다."""
    print("\n>>> 새로운 물품 입고 시도...")
    receiving_sector = self.get_sector(SectorName.RECEIVING)
    return receiving_sector.add_stock()

  def classify_and_store(self, classified_color: ItemColor) -> bool:
    """입고 구역의 물품을 분류하여 해당 색상 저장고로 옮깁니다."""
    print(f"\n>>> 입고 구역 물품을 '{classified_color.name}'(으)로 분류 및 저장 시도...")
    if classified_color == ItemColor.UNKNOWN:
        print("실패: UNKNOWN 상태로는 저장 구역으로 옮길 수 없습니다.")
        return False
        
    receiving_sector = self.get_sector(SectorName.RECEIVING)
    storage_name = self._get_storage_sector_name(classified_color)
    storage_sector = self.get_sector(storage_name)

    if receiving_sector.stock == 0:
        print("실패: 입고 구역에 분류할 물품이 없습니다.")
        return False

    if not storage_sector.is_available_for_storage:
        print(f"실패: '{storage_name.name}' 저장 구역이 가득 찼거나 사용할 수 없습니다.")
        return False

    # 트랜잭션: 한쪽 성공 시 다른 쪽도 반드시 성공해야 함
    if receiving_sector.remove_stock():
        if storage_sector.add_stock():
            print("성공: 입고 -> 저장 구역으로 물품 이동 완료.")
            return True
        else:
            # 롤백: 저장 실패 시 입고 구역 재고 원상복구
            receiving_sector.add_stock()
            print("오류: 저장 구역에 추가 실패. 입고 구역 재고를 롤백합니다.")
            return False
    return False

  def prepare_for_shipping(self, color: ItemColor) -> bool:
    """저장 구역의 물품을 출고 구역(SHIPPING)으로 옮깁니다."""
    print(f"\n>>> '{color.name}' 색상 물품 출고 준비 시도...")
    storage_name = self._get_storage_sector_name(color)
    if not storage_name:
        print("실패: 유효하지 않은 색상입니다.")
        return False

    storage_sector = self.get_sector(storage_name)
    shipping_sector = self.get_sector(SectorName.SHIPPING)

    if storage_sector.stock == 0:
        print(f"실패: '{storage_name.name}'에 출고할 재고가 없습니다.")
        return False

    if storage_sector.remove_stock():
        if shipping_sector.add_stock():
            print("성공: 저장 -> 출고 구역으로 물품 이동 완료.")
            return True
        else:
            storage_sector.add_stock() # 롤백
            print("오류: 출고 구역에 추가 실패. 저장 구역 재고를 롤백합니다.")
            return False
    return False

  def display_all_statuses(self):
    print("\n--- 전체 구역 현재 상태 ---")
    for name, sector in self.sectors.items():
      capacity_str = "무제한" if sector.capacity == 0 else str(sector.capacity)
      print(f"- {name.name:<15}: {sector.status.name:<12} | 재고: {sector.stock}/{capacity_str}")
    print("--------------------------")

if __name__ == '__main__':
  # SectorManager 인스턴스 생성
  manager = SectorManager()
  
  # 입고(RECEIVING) 구역의 모터 상태 확인
  receiving_sector = manager.get_sector(SectorName.RECEIVING)
  receiving_sector.display_motor_statuses()
  
  # SERVO1 모터 켜기
  print("\n>>> SERVO1 모터를 켭니다...")
  receiving_sector.turn_on_motor("SERVO1")
  
  # 현재 SERVO1 모터 상태 확인
  servo_status = receiving_sector.get_motor_status("SERVO1")
  print(f"현재 SERVO1 모터 상태: {servo_status.name if servo_status else '알 수 없음'}")
  
  # 입고 구역의 모든 모터 상태 다시 확인
  receiving_sector.display_motor_statuses()
  
  # SERVO1 모터 끄기
  print("\n>>> SERVO1 모터를 끕니다...")
  receiving_sector.turn_off_motor("SERVO1")
  receiving_sector.display_motor_statuses()

  # 존재하지 않는 모터 제어 시도
  print("\n>>> 존재하지 않는 모터를 제어합니다...")
  receiving_sector.turn_on_motor("MOTOR_X")