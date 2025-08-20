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
  AVAILABLE = auto()    # 사용 가능 (재고 꽉 차지 않음)
  PROCESSING = auto()   # 사용 중 (센서 처리작업 중)
  UNAVAILABLE = auto()  # 사용 불가능 (오류 등)
  FULL = auto()         # 가득 참

# 아이템 상태 관리 enum?
# 모터 / 센서 상태 관리 enum?

'''
구역 PROCESSING 상태?
1. 센서 처리 중 상태?
2. 재고가 1개 이상 있는 상태?
'''

# --- Sector 클래스 (재고/용량 기능 추가) ---

class Sector:
  """
  하나의 구역(Sector)을 나타내는 클래스.
  상태, 재고, 용량 정보를 포함하고 관련 메서드를 제공합니다.
  """
  def __init__(self, name: SectorName, capacity: int = 0, sensor_list: Optional[List[str]] = None, motor_list: Optional[List[str]] = None):
    """
    Sector 객체를 초기화합니다.

    :param name: 구역의 고유 이름 (SectorName Enum)
    :param capacity: 이 구역이 수용할 수 있는 최대 물품 수 (0 : 제한 없음 / 양수 : 해당 수로 구역의 최대 물품 수 제한)
    :param sensor_list: 할당된 센서 ID 리스트
    :param motor_list: 할당된 모터 ID 리스트
    """
    self.name = name
    self.capacity = capacity
    self.stock: int = 0 # 현재 물품 재고 (0 : 재고 제한 없음)
    self.sensor_list: List[str] = sensor_list if sensor_list is not None else []
    self.motor_list: List[str] = motor_list if motor_list is not None else []
    self.status: SectorStatus = SectorStatus.UNAVAILABLE

  def update_status(self, new_status: SectorStatus):
    """구역의 상태를 변경합니다."""
    if self.status != new_status:
      print(f"[{self.name.name}] 상태 변경: {self.status.name} -> {new_status.name}")
      self.status = new_status

  def add_stock(self, quantity : int = 1) -> bool:
    """재고 추가 기능. 성공시 True / 실패시 False 반환"""
    # capacity값이 0이면 재고 제한 없음
    if self.capacity != 0 and self.stock + quantity > self.capacity:
      print(f"[{self.name.name}] 재고 추가 실패: 용량 초과 (현재: {self.stock}, 용량: {self.capacity})")
      return False
    
    self.stock += quantity
    print(f"[{self.name.name}] 재고 추가: {self.stock - quantity} -> {self.stock}")
    
    if self.capacity != 0 and self.stock == self.capacity:
      self.update_status(SectorStatus.FULL)
    return True

  def remove_stock(self, quantity: int = 1) -> bool:
    """재고를 제거합니다. 성공 시 True, 실패(재고 부족) 시 False를 반환합니다."""
    if self.stock - quantity >= 0:
      self.stock -= quantity
      print(f"[{self.name.name}] 재고 제거: {self.stock + quantity} -> {self.stock}")
      # 재고가 0이 되면 상태를 AVAILABLE로 변경
      if self.stock == 0:
        self.update_status(SectorStatus.AVAILABLE)

      return True
    else:
      print(f"[{self.name.name}] 재고 제거 실패: 재고 부족 (현재: {self.stock})")
      return False

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

# --- SectorManager 클래스 (재고 관리 로직 추가) ---
  # - 싱글톤 패턴 사용 : 구역에 대한 인스턴스는 1개만 생성

class SectorManager:
  """
  전체 구역을 중앙에서 관리하는 싱글톤(Singleton) 클래스.
  재고 관리 및 물품 입/출고 로직을 포함합니다.
  """
  _instance = None

  def __new__(cls, *args, **kwargs):
    if not cls._instance:
      cls._instance = super(SectorManager, cls).__new__(cls, *args, **kwargs)
    return cls._instance

  def __init__(self):
    # __new__에서 여러 번 호출되는 것을 방지하기 위한 초기화 플래그
    if not hasattr(self, 'initialized'):
      self.sectors: Dict[SectorName, Sector] = {
        SectorName.RECEIVING: Sector(
            name=SectorName.RECEIVING,
            capacity=0,
            sensor_list=["RGB", "PROXI"], # 컬러 센서 / 근접 센서 
            motor_list=["SERVO"]
        ),
        SectorName.RED_STORAGE: Sector(
            name=SectorName.RED_STORAGE, 
            capacity=3,
            sensor_list=["PROXI"], 
            motor_list=["SERVO"]
        ),
        SectorName.GREEN_STORAGE: Sector(
            name=SectorName.GREEN_STORAGE, 
            capacity=3,
            sensor_list=["PROXI"], 
            motor_list=["SERVO"]
        ),
        SectorName.YELLOW_STORAGE: Sector(
            name=SectorName.YELLOW_STORAGE, 
            capacity=3,
            sensor_list=["PROXI"], 
            motor_list=["SERVO"]
        ),
        SectorName.SHIPPING: Sector(
            name=SectorName.SHIPPING, 
            capacity=0,
            sensor_list=["RGB", "PROXI"], 
            motor_list=["SERVO"]
        )
      }
      self.initialized = True

  def initialize_all_sectors(self):
    """모든 구역의 상태를 'AVAILABLE'로 초기화합니다."""
    print("--- 모든 구역을 사용 가능(AVAILABLE) 상태로 초기화합니다. ---")
    for sector in self.sectors.values():
      sector.update_status(SectorStatus.AVAILABLE)

  def get_sector(self, name: SectorName) -> Sector:
    """이름으로 특정 구역 객체를 가져옵니다."""
    return self.sectors[name]
  
  def update_sector_status(self, name: SectorName, status: SectorStatus):
    """특정 구역의 상태를 업데이트합니다."""
    if name in self.sectors:
      self.sectors[name].update_status(status)
    else:
      print(f"오류: {name}이라는 이름의 구역을 찾을 수 없습니다.")

  def _get_storage_sector_name(self, color: ItemColor) -> SectorName:
    """아이템 색상에 해당하는 저장 구역 이름을 반환합니다."""
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

    if not storage_sector.is_available_for_storage:
        print(f"실패: '{storage_name.name}' 저장 구역이 가득 찼거나 사용할 수 없습니다.")
        return False

    if receiving_sector.stock == 0:
        print("실패: 입고 구역에 분류할 물품이 없습니다.")
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
