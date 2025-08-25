# LMS 재고 관리자 데모

import sys
import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

# config 임포트
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import *

@dataclass
class InventoryItem:
    """재고 아이템"""
    color: ItemColor
    sector: SectorName
    timestamp: float

@dataclass
class SectorInfo:
    """구역 정보"""
    name: SectorName
    capacity: int
    current_stock: int
    items: List[InventoryItem]
    status: SectorStatus

class InventoryManagerDemo:
    """재고 관리자 데모"""
    
    def __init__(self):
        # 구역 정보 초기화
        self.sectors = {}
        for sector_name, capacity in SECTOR_CAPACITY.items():
            self.sectors[sector_name] = SectorInfo(
                name=sector_name,
                capacity=capacity,
                current_stock=0,
                items=[],
                status=SectorStatus.AVAILABLE
            )
        
        # 누적 통계
        self.cumulative_stats = {
            'total_received': 0,
            'total_shipped': 0,
            'total_red_processed': 0,
            'total_green_processed': 0,
            'total_yellow_processed': 0
        }
        
        # 스레드 안전성을 위한 락
        self.lock = threading.RLock()
        
    def add_items_to_receiving(self, red_count: int, green_count: int) -> bool:
        """입고 구역에 물품 추가"""
        with self.lock:
            try:
                receiving_sector = self.sectors[SectorName.RECEIVING]
                current_time = time.time()
                
                # RED 물품 추가
                for _ in range(red_count):
                    item = InventoryItem(
                        color=ItemColor.RED,
                        sector=SectorName.RECEIVING,
                        timestamp=current_time
                    )
                    receiving_sector.items.append(item)
                
                # GREEN 물품 추가
                for _ in range(green_count):
                    item = InventoryItem(
                        color=ItemColor.GREEN,
                        sector=SectorName.RECEIVING,
                        timestamp=current_time
                    )
                    receiving_sector.items.append(item)
                
                # 재고 수량 업데이트
                receiving_sector.current_stock = len(receiving_sector.items)
                
                # 누적 통계 업데이트
                self.cumulative_stats['total_received'] += red_count + green_count
                self.cumulative_stats['total_red_processed'] += red_count
                self.cumulative_stats['total_green_processed'] += green_count
                
                print(f"✓ 입고 완료: RED={red_count}, GREEN={green_count}")
                print(f"  입고구역 현재 재고: {receiving_sector.current_stock}")
                
                # 자동 분류 시작
                self.auto_sort_items()
                
                return True
                
            except Exception as e:
                print(f"✗ 입고 오류: {e}")
                return False
    
    def auto_sort_items(self):
        """입고 구역 물품을 색상별 저장구역으로 자동 분류"""
        with self.lock:
            receiving_sector = self.sectors[SectorName.RECEIVING]
            
            # 색상별로 분류
            items_to_move = {
                ItemColor.RED: [],
                ItemColor.GREEN: [],
                ItemColor.YELLOW: []
            }
            
            for item in receiving_sector.items[:]:  # 복사본으로 반복
                if item.color in items_to_move:
                    items_to_move[item.color].append(item)
            
            # 각 색상별로 이동 처리
            for color, items in items_to_move.items():
                if not items:
                    continue
                
                target_sector_name = self.get_storage_sector_for_color(color)
                target_sector = self.sectors[target_sector_name]
                
                # 용량 확인
                available_space = target_sector.capacity - target_sector.current_stock
                if target_sector.capacity == 0:  # 무제한
                    available_space = len(items)
                
                movable_count = min(len(items), available_space)
                
                if movable_count > 0:
                    # 아이템 이동
                    items_to_move_now = items[:movable_count]
                    
                    for item in items_to_move_now:
                        # 입고구역에서 제거
                        receiving_sector.items.remove(item)
                        
                        # 저장구역으로 이동
                        item.sector = target_sector_name
                        target_sector.items.append(item)
                    
                    # 재고 수량 업데이트
                    receiving_sector.current_stock = len(receiving_sector.items)
                    target_sector.current_stock = len(target_sector.items)
                    
                    color_name = color.name
                    sector_name = target_sector_name.name
                    print(f"  → {color_name} {movable_count}개를 {sector_name}로 이동")
                
                if movable_count < len(items):
                    remaining = len(items) - movable_count
                    print(f"  ⚠ {color.name} {remaining}개는 저장구역 용량 부족으로 대기")
    
    def ship_items(self, red_count: int, green_count: int, yellow_count: int) -> bool:
        """저장구역에서 출고구역으로 물품 출고"""
        with self.lock:
            try:
                # 재고 확인
                if not self.check_stock_availability(red_count, green_count, yellow_count):
                    print("✗ 출고 실패: 재고 부족")
                    return False
                
                # 각 색상별로 출고 처리
                shipment_plan = [
                    (ItemColor.RED, red_count, SectorName.RED_STORAGE),
                    (ItemColor.GREEN, green_count, SectorName.GREEN_STORAGE),
                    (ItemColor.YELLOW, yellow_count, SectorName.YELLOW_STORAGE)
                ]
                
                shipping_sector = self.sectors[SectorName.SHIPPING]
                total_shipped = 0
                
                for color, count, source_sector_name in shipment_plan:
                    if count == 0:
                        continue
                    
                    source_sector = self.sectors[source_sector_name]
                    
                    # 해당 색상의 아이템 찾기
                    items_to_ship = []
                    for item in source_sector.items:
                        if item.color == color and len(items_to_ship) < count:
                            items_to_ship.append(item)
                    
                    # 아이템 이동
                    for item in items_to_ship:
                        source_sector.items.remove(item)
                        item.sector = SectorName.SHIPPING
                        shipping_sector.items.append(item)
                    
                    # 재고 수량 업데이트
                    source_sector.current_stock = len(source_sector.items)
                    total_shipped += len(items_to_ship)
                    
                    if items_to_ship:
                        color_name = color.name
                        print(f"  → {color_name} {len(items_to_ship)}개를 SHIPPING으로 이동")
                
                # 출고구역 재고 업데이트
                shipping_sector.current_stock = len(shipping_sector.items)
                
                # 누적 통계 업데이트
                self.cumulative_stats['total_shipped'] += total_shipped
                
                print(f"✓ 출고 완료: 총 {total_shipped}개")
                print(f"  출고구역 현재 재고: {shipping_sector.current_stock}")
                
                return True
                
            except Exception as e:
                print(f"✗ 출고 오류: {e}")
                return False
    
    def check_stock_availability(self, red_count: int, green_count: int, yellow_count: int) -> bool:
        """재고 가용성 확인"""
        red_available = len([item for item in self.sectors[SectorName.RED_STORAGE].items 
                           if item.color == ItemColor.RED])
        green_available = len([item for item in self.sectors[SectorName.GREEN_STORAGE].items 
                             if item.color == ItemColor.GREEN])
        yellow_available = len([item for item in self.sectors[SectorName.YELLOW_STORAGE].items 
                              if item.color == ItemColor.YELLOW])
        
        return (red_available >= red_count and 
                green_available >= green_count and 
                yellow_available >= yellow_count)
    
    def get_storage_sector_for_color(self, color: ItemColor) -> SectorName:
        """색상에 맞는 저장구역 반환"""
        color_to_sector = {
            ItemColor.RED: SectorName.RED_STORAGE,
            ItemColor.GREEN: SectorName.GREEN_STORAGE,
            ItemColor.YELLOW: SectorName.YELLOW_STORAGE
        }
        return color_to_sector.get(color, SectorName.RECEIVING)
    
    def get_current_stock(self) -> Dict[str, int]:
        """현재 재고 현황 반환 (AU 데이터용)"""
        with self.lock:
            return {
                'receiving': self.sectors[SectorName.RECEIVING].current_stock,
                'red_storage': self.sectors[SectorName.RED_STORAGE].current_stock,
                'green_storage': self.sectors[SectorName.GREEN_STORAGE].current_stock,
                'yellow_storage': self.sectors[SectorName.YELLOW_STORAGE].current_stock,
                'shipping': self.sectors[SectorName.SHIPPING].current_stock,
                'receiving_total': self.cumulative_stats['total_received'],
                'shipping_total': self.cumulative_stats['total_shipped']
            }
    
    def show_detailed_status(self):
        """상세 재고 현황 출력"""
        print("\n=== 상세 재고 현황 ===")
        
        with self.lock:
            for sector_name, sector_info in self.sectors.items():
                print(f"\n{sector_info.name.name}:")
                print(f"  용량: {sector_info.capacity if sector_info.capacity > 0 else '무제한'}")
                print(f"  현재 재고: {sector_info.current_stock}")
                print(f"  상태: {sector_info.status.name}")
                
                # 색상별 세부 내역
                if sector_info.items:
                    color_counts = {}
                    for item in sector_info.items:
                        color = item.color.name
                        color_counts[color] = color_counts.get(color, 0) + 1
                    
                    print(f"  색상별 내역: {color_counts}")
        
        print(f"\n=== 누적 통계 ===")
        for stat_name, value in self.cumulative_stats.items():
            print(f"{stat_name}: {value}")
    
    def simulate_operations(self):
        """운영 시뮬레이션"""
        print("\n=== 재고 관리 시뮬레이션 ===")
        
        # 1. 초기 입고
        print("\n1. 초기 입고 (RED:10, GREEN:5)")
        self.add_items_to_receiving(10, 5)
        
        # 2. 추가 입고
        print("\n2. 추가 입고 (RED:3, GREEN:7)")
        self.add_items_to_receiving(3, 7)
        
        # 3. 출고 시도
        print("\n3. 출고 시도 (RED:5, GREEN:3, YELLOW:2)")
        self.ship_items(5, 3, 2)
        
        # 4. 재고 부족 출고 시도
        print("\n4. 재고 부족 출고 시도 (RED:20, GREEN:20, YELLOW:20)")
        self.ship_items(20, 20, 20)
        
        # 5. 현재 상태 출력
        self.show_detailed_status()

def main():
    """메인 함수"""
    print("=== LMS 재고 관리자 데모 ===")
    
    inventory = InventoryManagerDemo()
    
    try:
        # 시뮬레이션 실행
        inventory.simulate_operations()
        
        # 대화형 모드
        print("\n=== 대화형 모드 ===")
        print("명령어: receive <red> <green>, ship <red> <green> <yellow>, status, quit")
        
        while True:
            try:
                command = input("\ninventory> ").strip().split()
                if not command:
                    continue
                
                if command[0] == 'quit':
                    break
                elif command[0] == 'receive' and len(command) >= 3:
                    red = int(command[1])
                    green = int(command[2])
                    inventory.add_items_to_receiving(red, green)
                elif command[0] == 'ship' and len(command) >= 4:
                    red = int(command[1])
                    green = int(command[2])
                    yellow = int(command[3])
                    inventory.ship_items(red, green, yellow)
                elif command[0] == 'status':
                    inventory.show_detailed_status()
                elif command[0] == 'stock':
                    stock = inventory.get_current_stock()
                    print(f"현재 재고: {stock}")
                else:
                    print("잘못된 명령어입니다.")
                    
            except ValueError:
                print("숫자를 올바르게 입력해주세요.")
            except KeyboardInterrupt:
                break
    
    except KeyboardInterrupt:
        pass
    
    print("\n재고 관리자 데모 종료")

if __name__ == "__main__":
    main()