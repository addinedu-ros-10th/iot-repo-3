#include <ESP32Servo.h>
#include <WiFi.h>
#include <esp_now.h>


uint8_t peerMac[6] = {0x08,0xA6,0xF7,0x21,0xAC,0xF4}; // Jeao_ESP32 MAC 08:A6:F7:21:AC:F4

Servo myservo;
const char* ssid = "AIE_509_2.4G";          //공유기 이름
const char* password = "addinedu_class1";    //공유기 비밀번호

const char* host = "192.168.0.100"; // Python 서버 PC IP
const uint16_t port = 8100;

void steppingRun(bool run, short speed);
int colorSearch(bool led);
void sendData(const char* msg);

struct RunTime {
unsigned long led_Time;
};

RunTime run_T;

const short step_s1 = 27, step_s2 = 14, step_s3 = 12, step_s4 = 13;
const short servo_pin = 15;
const short col_s0 = 32, col_s1 = 33, col_s2 = 25, col_s3 = 26, col_out = 34, col_led = 2;
int steps_cw[8] = { 0x01, 0x03, 0x02, 0x06, 0x04, 0x0C, 0x08, 0x09 };
int steps_ccw[8] = { 0x09, 0x08, 0x0C, 0x04, 0x06, 0x02, 0x03, 0x01 };
int step_index = 0;
short angle = 175;
bool col_status = false;
bool block = true;
char u_c[10] = "";
bool msg_status = false;

typedef struct {
char value[10];
} DataPacket;

volatile DataPacket latestData;
volatile bool newDataReceived = false;

void onRecv(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len){
  if(len == sizeof(DataPacket)){
    memcpy((void*)&latestData, (const void*)incomingData, sizeof(DataPacket));
    newDataReceived = true;
  }
}

DataPacket p;

void setup() {
  Serial.begin(115200);
  Serial.println("Unloading!");
  WiFi.begin(ssid, password);   //공유기 접속 시도
  Serial.print("Wi-Fi 연결중");
  while(WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi 연결 성공!");
  Serial.print("IP 주소: ");
  Serial.println(WiFi.localIP());   // ESP32의 IP 확인
  Serial.print("Unloading ESP32 MAC : ");
  Serial.println(WiFi.macAddress());

    // 스텝모터 스탭별 핀모드 적용
  pinMode(step_s1, OUTPUT);
  pinMode(step_s2, OUTPUT);
  pinMode(step_s3, OUTPUT);
  pinMode(step_s4, OUTPUT);

  //서보모터 초기 셋팅 위치
  myservo.attach(servo_pin);
  myservo.write(angle);
  // myservo.detach();       //서보모터 연결 끊기
  delay(500);

  // 컬러센서 셋팅 및 led 선언
  pinMode(col_s0, OUTPUT);
  pinMode(col_s1, OUTPUT);
  pinMode(col_s2, OUTPUT);
  pinMode(col_s3, OUTPUT);
  pinMode(col_led, OUTPUT);
  pinMode(col_out, INPUT);
  digitalWrite(col_led, HIGH);
  col_status = true;

  // RGB 주파수 스케일 설정
  digitalWrite(col_s0, HIGH);
  digitalWrite(col_s1, LOW);
  
  //컬러센서 LED 시간 초기화
  run_T.led_Time = 0;
  delay(1000);
  
  WiFi.mode(WIFI_STA);
  if(esp_now_init() != ESP_OK)
  {
    Serial.println("ESP-NOW init fail");
  }

  // 피어 등록
  esp_now_peer_info_t peer{};
  memcpy(peer.peer_addr, peerMac, 6);
  peer.channel = 0;
  peer.encrypt = false;
  esp_now_add_peer(&peer);
    // 수신 콜백 등록
  esp_now_register_recv_cb(onRecv);
}
void loop() {
  // put your main code here, to run repeatedly:
  unsigned long now = millis();
  int res = 0;

    //수신 부분
  if(newDataReceived)
  {
    Serial.print("수신 성공: ");
    char buffer[10];
    strcpy(buffer, (const char*)latestData.value);
    strcpy(p.value, buffer);
    Serial.println(p.value);  // 바로 출력 가능
    newDataReceived = false;
    //msg_status = false;
  }

  
  steppingRun(block, 60, &col_status);
  if(strcmp(p.value, "CI") == 0)
  {
    Serial.println("Servo Move!!");
    myservo.write(90);
    delay(500);
    myservo.write(175);
    delay(500);
    msg_status = false;
  }
  else
  {
    if(col_status && (now - run_T.led_Time >= 200) && !msg_status)
    {
      run_T.led_Time = now; 
      res = colorSearch(col_status); 
      if(res != 0) 
      { 
        block = false; 
        Serial.print("Color return: "); 
        Serial.println(res); 
        switch(res) 
        { 
          case 1:     //빨강 
            Serial.println("Red Shoot!!"); 
            strcpy(u_c, "UCR"); 
            break; 
          case 2:     //초록 
            Serial.println("Green Shoot!!"); 
            strcpy(u_c, "UCG"); 
            break; 
          case 3:     //노랑 
            Serial.println("Yellow Shoot!!"); 
            strcpy(u_c, "UCY");  
            break; 
          default: 
            Serial.println("색상 인식 오류"); 
            break; 
        } 
      }

      sendData(u_c);
    }
  }
  
}
//_________________________________________________________
void steppingRun(bool run, short speed, bool *col)
{
  speed = map(speed, 0, 100, 1500, 50);
  if (run)
  {
    if(! *col)
    {
      Serial.println("Color ON!");
      msg_status = false;
      *col = true;
    }
    digitalWrite(step_s1, bitRead(steps_cw[step_index], 0)); 
    digitalWrite(step_s2, bitRead(steps_cw[step_index], 1)); 
    digitalWrite(step_s3, bitRead(steps_cw[step_index], 2)); 
    digitalWrite(step_s4, bitRead(steps_cw[step_index], 3)); 
    step_index = (step_index + 1) % 8; 
    delayMicroseconds(speed);
  }
  else
  {
    step_index = 0;
  }
}
int colorSearch(bool col)
  {
  if (col)
  {
    //Red
    digitalWrite(col_s2, LOW);
    digitalWrite(col_s3, LOW);
    long redFrequency = pulseIn(col_out, LOW, 100000);
    // Green
    digitalWrite(col_s2, HIGH);
    digitalWrite(col_s3, HIGH);
    long greenFrequency = pulseIn(col_out, LOW, 100000);
    // Blue
    digitalWrite(col_s2, LOW);
    digitalWrite(col_s3, HIGH);
    long blueFrequency = pulseIn(col_out, LOW, 100000); 
    Serial.print("R= "); Serial.print(redFrequency); 
    Serial.print(" G= "); Serial.print(greenFrequency); 
    Serial.print(" B= "); Serial.println(blueFrequency); 
    short result; 
    if (redFrequency > 30 && redFrequency < 100 && greenFrequency > 150) { 
      result = 1; 
    } 
    else if (redFrequency > 100 && greenFrequency > 50 && greenFrequency < 100) { 
      result = 2; 
    } 
    else if (redFrequency < 100 && greenFrequency < 100) { 
      result = 3; 
    } 
    else { 
      result = 0; 
    } 
    return result;
  }
}

void sendData(const char* msg) {
  if (strlen(msg) != 0)
  {
      // 문자열을 구조체에 복사
    strncpy(p.value, msg, sizeof(p.value));
    p.value[sizeof(p.value) - 1] = '\0'; // NULL 종료 보장

    // ESP-NOW 송신
    esp_err_t result = esp_now_send(peerMac, (uint8_t*)&p, sizeof(p));
    if(result == ESP_OK) {
      Serial.println("송신 성공: " + String(p.value));
      msg_status = true;
    } else {
      Serial.println("송신 실패");
    }
  }
}