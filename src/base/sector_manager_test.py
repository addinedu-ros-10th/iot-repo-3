from sector_library import SectorManager, SectorName, SectorStatus, ItemColor

if __name__ == "__main__":
  # SectorManager 인스턴스 생성 (싱글톤)
  manager = SectorManager()
  
  # 1. 모든 구역상태 확인
  manager.display_all_statuses()
  
  # 2. 구역을 사용 가능 / 처리중 상태로 변경
  manager.update_sector_status(SectorName.RECEIVING, SectorStatus.AVAILABLE)
  manager.update_sector_status(SectorName.RED_STORAGE, SectorStatus.AVAILABLE)
  manager.update_sector_status(SectorName.GREEN_STORAGE, SectorStatus.AVAILABLE)
  manager.update_sector_status(SectorName.YELLOW_STORAGE, SectorStatus.UNAVAILABLE)
  manager.update_sector_status(SectorName.SHIPPING, SectorStatus.AVAILABLE)

  # 2. 시나리오: 새로운 물품 3개 입고 (RECEIVING 구역)
  print("\n--- [시나리오 1: 새로운 물품 3개 입고] ---")
  manager.receive_new_item()
  manager.receive_new_item()
  manager.receive_new_item()
  manager.display_all_statuses()

  # 3. 시나리오: 입고된 물품 분류 및 저장
  print("\n--- [시나리오 2: 물품 분류 및 저장] ---")
  # 첫 번째 물품은 RED로 분류
  manager.classify_and_store(ItemColor.RED)
  # 두 번째 물품은 GREEN으로 분류
  manager.classify_and_store(ItemColor.GREEN)
  manager.display_all_statuses()

  # 4. 시나리오: RED 저장고 가득 채우기 (용량: 3)
  print("\n--- [시나리오 3: RED 저장고 채우기] ---")
  manager.receive_new_item() # 분류할 물품 추가 입고
  manager.classify_and_store(ItemColor.RED)
  
  manager.receive_new_item() # 분류할 물품 추가 입고
  manager.classify_and_store(ItemColor.RED)
  manager.display_all_statuses()

  # 5. 시나리오: 꽉 찬 RED 저장고에 추가 저장 시도 (실패)
  print("\n--- [시나리오 4: 꽉 찬 RED 저장고에 추가 저장 시도] ---")
  manager.receive_new_item() # 분류할 물품 추가 입고
  manager.classify_and_store(ItemColor.RED) # 이 과정은 실패해야 함
  manager.display_all_statuses() # RECEIVING 재고는 1, RED_STORAGE 재고는 3으로 유지되어야 함

  # 6. 시나리오: GREEN 물품 출고 준비
  print("\n--- [시나리오 5: GREEN 물품 출고 준비] ---")
  manager.prepare_for_shipping(ItemColor.GREEN)
  manager.display_all_statuses()

  # 7. 시나리오: UNAVAILABLE 구역에서 물품 출고 시도 (실패)
  print("\n--- [시나리오 6: 재고 없는 YELLOW 물품 출고 시도] ---")
  manager.prepare_for_shipping(ItemColor.YELLOW)
  manager.display_all_statuses()