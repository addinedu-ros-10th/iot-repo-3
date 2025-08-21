# TCP 통신 인터페이스 명세서

## 1. 기본 통신 정보

* **서버**: LMS
* **클라이언트**: GUI
* **프로토콜**: TCP/IP
* **데이터 형식**: 바이너리 (고정 크기 필드)
* **종료 문자**: 모든 메시지는 `\n` (ASCII 0x0A) 문자로 끝나야 합니다.

---

## 2. 명령어 요약 (Command Summary)

GUI에서 LMS로 전송할 수 있는 명령어 목록입니다.

| Command | Full Name | Description |
| :--- | :--- | :--- |
| **RS** | Receive Stock | 입고 구역(**RECEIVING**)의 현재 재고 수량을 요청합니다. |
| **SS** | Shipping Stock | 출고 구역(**SHIPPING**)의 현재 재고 수량을 요청합니다. |
| **CS** | Current Stock | 특정 색상 저장 구역(**STORAGE**)의 현재 재고 수량을 요청합니다. |
| **AS** | All Stock | 모든 구역의 현재 재고 수량을 한 번에 요청합니다. |
| **RI** | Receive Item | 입고 구역(**RECEIVING**)으로 사용자가 요청한 수량만큼 새로운 물품을 입고합니다. |
| **SI** | Ship Item | 특정 색상 저장 구역(**STORAGE**)에서 출고 구역(**SHIPPING**)으로 물품 1개를 이동합니다. |
| **SO (데모 명령어)** | Sort Item | 입고 구역(RECEIVING)의 물품을 특정 색상 저장 구역(STORAGE) 으로 이동시키는 테스트 명령 <br> 실제로는 로봇이 자동으로 물품을 분류 / 보관구역으로 물품을 이동시킴 |

---

## 3. 데이터 형식 정의

### 3.1 GUI → LSM (요청 형식)

* **Command** (2 Bytes): ASCII 문자열 (예: "RS")
* **Data** (4 Bytes): 명령어에 필요한 추가 데이터. 데이터가 없는 경우 `0x00`으로 채웁니다.
* **End** (1 Byte): `\n` (0x0A)

| Command | Data (4 Bytes) | 설명 |
| :--- | :--- | :--- |
| **RS** | `0x00000000` | 데이터 없음 |
| **SS** | `0x00000000` | 데이터 없음 |
| **CS** | `[Color Code]` | `Color Code` (1 Byte): `0x01` (RED), `0x02` (GREEN), `0x03` (YELLOW) |
| **AS** | `0x00000000` | 데이터 없음 |
| **RI** | `[입고할 수량 (int)]` | 16진수 형태로 제공 |
| **SI** | `[Color Code]` | `Color Code` (1 Byte): `0x01` (RED), `0x02` (GREEN), `0x03` (YELLOW) |
| **SO** | `[Color Code]` | `Color Code` (1 Byte): `0x01` (RED), `0x02` (GREEN), `0x03` (YELLOW) |

**참고**: `[Color Code]`는 4바이트 Data 필드의 첫 1바이트에 위치하며, 나머지 3바이트는 `0x00`으로 처리합니다.

**예시**: 재고 입고 요청
`"RI" + 0x00000002 + \n` (`Command` + `Data` (입고할 수량) + `End`)

---

### 3.2 LSM → GUI (응답 형식)

* **Command** (2 Bytes): 요청받은 명령어와 동일한 ASCII 문자열
* **Status** (1 Byte): 처리 결과 상태 코드
* **Data** (가변): 요청에 대한 결과 데이터
* **End** (1 Byte): `\n` (0x0A)

**예시**: 입고 수량 조회 명령 성공 + 재고 2개
`"RS" + 0x00 + 0x00000002 + \n` (`Command` + `Status` + `Data` (재고 2개 16진수 표현) + `End`)

#### 상태 코드 (Status Code)

| Code | 의미 | 설명 |
| :--- | :--- | :--- |
| `0x00` | **SUCCESS** | 요청이 성공적으로 처리되었습니다. |
| `0x01` | **FAILURE** | 요청 처리에 실패했습니다. (예: 재고 부족, 용량 초과 등) |
| `0x02` | **INVALID_CMD** | 정의되지 않은 명령어입니다. |
| `0x03` | **INVALID_DATA** | 데이터가 유효하지 않습니다. (예: 잘못된 색상 코드) |

#### 명령어별 응답 데이터

| Command | Status | Data | 설명 |
| :--- | :--- | :--- | :--- |
| **RS** | `[Status]` | 4 Bytes | 입고 구역의 재고 수량 (Integer) |
| **SS** | `[Status]` | 4 Bytes | 출고 구역의 재고 수량 (Integer) |
| **CS** | `[Status]` | 4 Bytes | 요청한 색상 저장 구역의 재고 수량 (Integer) |
| **AS** | `[Status]` | 20 Bytes | 전체 구역의 재고 수량 (아래 표 참조) |
| **RI** | `[Status]` | 4 Bytes | 입고 성공 여부 / 입고 후 재고 수량 |
| **SI** | `[Status]` | - | 성공/실패 여부만 반환 |
| **SO** | `[Status]` | - | 성공/실패 여부만 반환 |

#### `AS` (All Stock) 명령어 응답 데이터 상세

`AS` 명령어의 응답 데이터는 총 20바이트이며, 각 구역의 재고 수량(4바이트 정수)이 아래 순서로 구성됩니다.

| 순서 | 필드명 | 크기 | 설명 |
| :--- | :--- | :--- | :--- |
| 1 | RECEIVING 재고 | 4 Bytes | 입고 구역 재고 수 |
| 2 | RED_STORAGE 재고 | 4 Bytes | 빨간색 저장 구역 재고 수 |
| 3 | GREEN_STORAGE 재고 | 4 Bytes | 초록색 저장 구역 재고 수 |
| 4 | YELLOW_STORAGE 재고 | 4 Bytes | 노란색 저장 구역 재고 수 |
| 5 | SHIPPING 재고 | 4 Bytes | 출고 구역 재고 수 |