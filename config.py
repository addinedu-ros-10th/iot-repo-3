#!/usr/bin/env python3
"""
IoT 시스템 통합 설정 파일
GUI-LMS 통신, 구역 관리, 재고 관리 등 모든 시스템 설정을 포함
"""

from enum import Enum, auto

# =============================================================================
# 시스템 Enum 정의
# =============================================================================

class SectorName(Enum):
    """각 구역의 고유한 이름을 정의"""
    RECEIVING = auto()        # 입고 전 물품, 색을 알 수 없는 물품 저장 (ItemColor : UNKNOWN)
    RED_STORAGE = auto()      # 입고 후 빨간색 물품 저장 구역 (ItemColor : RED)
    GREEN_STORAGE = auto()    # 입고 후 초록색 물품 저장 구역 (ItemColor : GREEN)
    YELLOW_STORAGE = auto()   # 입고 후 노란색 물품 저장 구역 (ItemColor : YELLOW)
    SHIPPING = auto()         # 출고 후 3색 물품 처리 구역   (ItemColor : R / G / Y)


class SectorType(Enum):
    """구역 타입"""
    RECEIVING = "RECEIVING"        # 입고 구역
    RED_STORAGE = "RED_STORAGE"    # 빨간색 저장 구역
    GREEN_STORAGE = "GREEN_STORAGE"  # 초록색 저장 구역
    YELLOW_STORAGE = "YELLOW_STORAGE"  # 노란색 저장 구역
    SHIPPING = "SHIPPING"          # 출고 구역


class ItemColor(Enum):
    """물품의 종류를 나타내는 색상"""
    UNKNOWN = auto()  # 입고 전 / 분류 실패
    RED = auto()
    GREEN = auto()
    YELLOW = auto()


class ColorCode(Enum):
    """색상 코드 정의"""
    RED = 0x01
    GREEN = 0x02
    YELLOW = 0x03


class SectorStatus(Enum):
    """구역 상태 정의"""
    AVAILABLE = auto()    # 사용 가능 (비어 있음)
    PROCESSING = auto()   # 사용 중 (물품 처리 중)
    UNAVAILABLE = auto()  # 사용 불가능 (오류 등)
    FULL = auto()         # 가득 참


class MotorStatus(Enum):
    """모터 상태 정의"""
    ON = auto()
    OFF = auto()

# =============================================================================
# 서버 및 통신 설정
# =============================================================================

# 서버 설정
SERVER_CONFIG = {
    'host': 'localhost',
    'port': 8100,
    'max_connections': 10,
    'client_timeout': 30.0,
    'buffer_size': 8192,
    'enable_keepalive': True,
    'keepalive_interval': 10.0,
    'max_clients': 10,
}

# 클라이언트 설정
CLIENT_CONFIG = {
    'server_host': 'localhost',
    'server_port': 8100,
    'connect_timeout': 5.0,
    'read_timeout': 10.0,
    'max_reconnect_attempts': 10,
    'reconnect_delay': 1.0,
    'retry_base_delay': 1.0,
    'retry_max_delay': 30.0,
    'auto_query_interval': 2.0,
    'heartbeat_interval': 5.0,
}

# 프로토콜 설정
PROTOCOL_CONFIG = {
    'message_header_size': 2,  # Command 필드
    'message_data_size': 14,   # Data 필드  
    'message_end_size': 1,     # End 필드
    'message_total_size': 17,  # 총 메시지 크기
    'response_timeout': 10.0,
    'max_message_queue': 100,
}

# =============================================================================
# 하드웨어 및 센서 설정
# =============================================================================

# 구역별 센서 설정
SECTOR_SENSORS = {
    SectorName.RECEIVING: ["RGB1", "RGB1"],
    SectorName.RED_STORAGE: ["PROXI1"],
    SectorName.GREEN_STORAGE: ["PROXI1"],
    SectorName.YELLOW_STORAGE: ["PROXI1"],
    SectorName.SHIPPING: ["RGB2"]
}

# 구역별 모터 설정
SECTOR_MOTORS = {
    SectorName.RECEIVING: ["SERVO1", "STEP1", "DC1"],
    SectorName.RED_STORAGE: ["STEP1"],
    SectorName.GREEN_STORAGE: ["STEP1"],
    SectorName.YELLOW_STORAGE: ["STEP1"],
    SectorName.SHIPPING: []
}

# 구역별 용량 설정
SECTOR_CAPACITY = {
    SectorName.RECEIVING: 0,      # 무제한
    SectorName.RED_STORAGE: 3,
    SectorName.GREEN_STORAGE: 3,
    SectorName.YELLOW_STORAGE: 3,
    SectorName.SHIPPING: 0        # 무제한
}

# =============================================================================
# 명령어 정의 (TCP 통신)
# =============================================================================

COMMANDS = {
    'RI': {
        'name': 'Receive Item',
        'description': '입고 구역으로 사용자가 요청한 수량만큼 새로운 물품 입고를 요청합니다.',
        'data_format': 'RED(2) + GREEN(2) + padding(10)',
        'response_expected': True,
        'response_data_format': 'Status(1)',
        'timeout': 10.0,
    },
    'AU': {
        'name': 'All Stock Update',
        'description': '모든 구역의 현재 재고 수량 및 입출고 누적 재고 업데이트를 전송합니다.',
        'data_format': 'RECEIVING재고(2) + RED_STORAGE재고(2) + GREEN_STORAGE재고(2) + YELLOW_STORAGE재고(2) + SHIPPING재고(2) + RECEIVING누적재고(2) + SHIPPING누적재고(2)',
        'response_expected': False,  # AU는 응답이 아닌 업데이트 데이터 전송
        'response_data_format': 'None',
        'timeout': 5.0,
    },
    'RH': {
        'name': 'Return Home',
        'description': '홈 위치로 이동을 요청합니다.',
        'data_format': 'Success(1) + padding(13)',
        'response_expected': True,
        'response_data_format': 'Status(1)',
        'timeout': 15.0,
    },
    'SI': {
        'name': 'Ship Item Request',
        'description': '보관 중인 물품(R/G/Y)의 출고를 요청합니다.',
        'data_format': 'RED(2) + GREEN(2) + YELLOW(2) + padding(8)',
        'response_expected': True,
        'response_data_format': 'Status(1)',
        'timeout': 10.0,
    },
    'RA': {
        'name': 'Request All stock',
        'description': 'AU 명령(전체 재고 업데이트)을 요청합니다.',
        'data_format': 'padding(14)',
        'response_expected': True,
        'response_data_format': 'AU Command + Stock Data(14)',
        'timeout': 5.0,
    },
}

# =============================================================================
# 상태 코드 정의
# =============================================================================

STATUS_CODES = {
    0x00: 'SUCCESS',
    0x01: 'FAILURE',
    0x02: 'INVALID_CMD',
    0x03: 'INVALID_DATA',
}