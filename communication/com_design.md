# 통합 통신 매니저 아키텍처 설계서

## 1. 개요
GUI 탭들과 LMS 간의 통신을 중앙집중화하여 관리하는 통합 통신 매니저 시스템 설계

## 2. 통신 프로토콜 분석

### 2.1 기본 통신 정보
- **프로토콜**: TCP/IP
- **데이터 형식**: 바이너리 (고정 크기 필드)
- **종료 문자**: \n (ASCII 0x0A)
- **메시지 구조**: Command(2B) + Data(14B) + End(1B) = 총 17바이트

### 2.2 주요 명령어
| Command | 설명 | 요청 데이터 | 응답 |
|---------|------|-------------|------|
| RI | 입고 요청 | RED(2B), GREEN(2B) 수량 | Status + 입고 결과 |
| SI | 출고 요청 | RED(2B), GREEN(2B), YELLOW(2B) 수량 | Status + 출고 결과 |
| AU | 전체 재고 업데이트 | 14바이트 재고 데이터 | 없음 |
| RA | 전체 재고 요청 | 빈 데이터 | AU 명령 수행 |
| RH | 홈 위치 복귀 | 성공 여부(1B) | Status |

### 2.3 재고 데이터 구조 (AU 명령어)
```
총 14바이트:
- RECEIVING 재고 (2B)
- RED_STORAGE 재고 (2B) 
- GREEN_STORAGE 재고 (2B)
- YELLOW_STORAGE 재고 (2B)
- SHIPPING 재고 (2B)
- RECEIVING 누적 재고 (2B)
- SHIPPING 누적 재고 (2B)
```

## 3. 아키텍처 설계

### 3.1 시스템 구조
```
GUI 탭들 ↔ ComManager ↔ LMS Server
    ↑           ↑
구독자 등록   TCP 통신 관리
콜백 처리     메시지 변환
```

### 3.2 ComManager 핵심 기능

#### 3.2.1 연결 관리
- TCP 소켓 연결/해제
- 연결 상태 모니터링
- 자동 재연결 메커니즘

#### 3.2.2 메시지 프로토콜 처리
- 바이너리 메시지 인코딩/디코딩
- 명령어별 데이터 패킹/언패킹
- 응답 파싱 및 상태 코드 처리

#### 3.2.3 구독자 관리
- 탭별 콜백 함수 등록
- 데이터 타입별 필터링
- 실시간 데이터 배포

#### 3.2.4 백그라운드 모니터링
- 주기적 재고 상태 수신 (RA/AU)
- 시스템 상태 모니터링
- 이벤트 기반 업데이트

### 3.3 탭별 통신 요구사항

#### 3.3.1 MainMonitorTab
- **수신**: 전체 재고 상태 (AU)
- **송신**: 없음 (모니터링 전용)
- **업데이트**: 실시간 재고 표시, 시스템 상태

#### 3.3.2 SensorsTab  
- **수신**: 센서/모터 상태 정보
- **송신**: 센서 제어 명령 (확장 가능)
- **업데이트**: 센서 상태 테이블, 모터 상태

#### 3.3.3 SystemManageTab
- **수신**: LMS 서버 연결 상태
- **송신**: 입고(RI), 출고(SI), 홈복귀(RH) 명령
- **업데이트**: 시스템 상태, 명령 실행 결과

## 4. 구현 전략

### 4.1 메시지 프로토콜 구현
```python
class MessageProtocol:
    @staticmethod
    def pack_command(cmd: str, data: bytes) -> bytes:
        """명령어를 바이너리로 패킹"""
        
    @staticmethod
    def unpack_response(response: bytes) -> dict:
        """응답을 파싱하여 딕셔너리로 반환"""
        
    @staticmethod
    def pack_stock_data(stock_info: dict) -> bytes:
        """재고 정보를 14바이트로 패킹"""
```

### 4.2 구독자 패턴 구현
```python
class ComManager:
    def register_subscriber(self, tab_name: str, callback: Callable, data_types: List[str]):
        """탭별 콜백 등록 (데이터 타입 필터 포함)"""
        
    def notify_subscribers(self, data_type: str, data: dict):
        """구독자들에게 데이터 배포"""
```

### 4.3 백그라운드 모니터링
```python
def _monitoring_loop(self):
    """백그라운드 모니터링 스레드"""
    while self.is_monitoring:
        # 1. RA 명령으로 재고 상태 요청
        # 2. AU 응답 수신 및 파싱
        # 3. 구독자들에게 데이터 배포
        # 4. 설정된 간격으로 대기
```

## 5. 데이터 흐름

### 5.1 입고 프로세스 (RI)
1. SystemManageTab → ComManager: RI 명령 전송
2. ComManager → LMS: 바이너리 메시지 전송
3. LMS → ComManager: 성공/실패 응답
4. ComManager → SystemManageTab: 결과 콜백
5. ComManager: RA 명령으로 재고 업데이트 요청
6. LMS → ComManager: AU 데이터 수신
7. ComManager → MainMonitorTab: 재고 업데이트 콜백

### 5.2 실시간 모니터링
1. ComManager: 주기적 RA 명령 전송
2. LMS → ComManager: AU 응답 수신
3. ComManager: 재고 데이터 파싱
4. ComManager → 구독자들: 업데이트 콜백 호출


## 향후 구현 (구현 안함)
```
## 6. 확장성 고려사항

### 6.1 새로운 명령어 추가
- MessageProtocol 클래스에 새 명령어 처리 메서드 추가
- 탭별 송신/수신 인터페이스 확장

### 6.2 다중 LMS 서버 지원
- ComManager에 서버 목록 관리 기능
- 로드 밸런싱 및 장애 복구 메커니즘

### 6.3 로깅 및 디버깅
- 통신 로그 기록
- 메시지 트래픽 모니터링
- 에러 처리 및 복구 전략

## 7. 성능 최적화

### 7.1 연결 풀링
- 재사용 가능한 TCP 연결 관리
- 연결 생성/해제 오버헤드 최소화

### 7.2 메시지 큐잉
- 비동기 메시지 처리
- 백프레셔 제어

### 7.3 캐싱
- 최근 재고 상태 캐싱
- 중복 요청 방지
```