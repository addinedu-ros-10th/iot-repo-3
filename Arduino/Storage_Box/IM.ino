#include <Stepper.h>

// 컬러센서, IR 및 LED 핀 설정 
const int COLOR_SENSOR_OUT_PIN = A15;
const int COLOR_SENSOR_LED_PIN = 49;
const int COLOR_SENSOR_S0_PIN = 50;
const int COLOR_SENSOR_S1_PIN = 51;
const int COLOR_SENSOR_S2_PIN = 52;
const int COLOR_SENSOR_S3_PIN = 53;

const int YELLOW_LED_PIN =  8;
const int GREEN_LED_PIN =  9;
const int RED_LED_PIN =  10;

const int YELLOW_IR_PIN =  11;
const int GREEN_IR_PIN =  12;
const int RED_IR_PIN =  13;
const int OUTPUT_IR_PIN =  68;
// 2048:한바퀴(360도), 1024:반바퀴(180도)...
// 모터 드라이브에 연결된 핀 IN4, IN2, IN3, IN1
const int STEPS_PER_REVOLUTION = 1024; 
Stepper YellowStepper(STEPS_PER_REVOLUTION,25,23,24,22);
Stepper GreenStepper(STEPS_PER_REVOLUTION,29,27,28,26);
Stepper RedStepper(STEPS_PER_REVOLUTION,33,31,32,30);

// IR 센서 상태 변수 초기화
bool last_green_state = HIGH;
bool last_yellow_state = HIGH;
bool last_red_state = HIGH;
bool last_out_state = HIGH;

const unsigned long COLOR_SENSOR_PERIOD = 100;
unsigned long color_sensor_prev_time = 0;


const unsigned long IR_SENSOR_PERIOD = 100;
unsigned long ir_sensor_prev_time = 0;

const unsigned long STEP_MOTOR_PERIOD = 500;
unsigned long y_step_motor_prev_time = 0;
unsigned long g_step_motor_prev_time = 0;
unsigned long r_step_motor_prev_time = 0;

unsigned int green_in_count = 0;
unsigned int yellow_in_count = 0;
unsigned int red_in_count = 0;
unsigned int out_total_count = 0;
unsigned int green_out_count = 0;
unsigned int yellow_out_count = 0;
unsigned int red_out_count = 0;

bool y_motor_flag = false;
bool g_motor_flag = false;
bool r_motor_flag = false;

bool out_check_flag = false;
int red_frequency, green_frequency, blue_frequency;

char cmd[2];
char send_buffer[16];
char result = '\0';

void setup() {
  Serial.begin(9600);
  pinMode(GREEN_IR_PIN, INPUT);
  pinMode(YELLOW_IR_PIN, INPUT);
  pinMode(RED_IR_PIN, INPUT);

  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);

  pinMode(COLOR_SENSOR_OUT_PIN, INPUT);
  pinMode(COLOR_SENSOR_LED_PIN, OUTPUT);
  pinMode(COLOR_SENSOR_S0_PIN, OUTPUT);
  pinMode(COLOR_SENSOR_S1_PIN, OUTPUT);
  pinMode(COLOR_SENSOR_S2_PIN, OUTPUT);
  pinMode(COLOR_SENSOR_S3_PIN, OUTPUT);

  GreenStepper.setSpeed(28); 
  YellowStepper.setSpeed(28); 
  RedStepper.setSpeed(28); 
  
  digitalWrite(COLOR_SENSOR_S0_PIN, LOW);
  digitalWrite(COLOR_SENSOR_S1_PIN, HIGH);
}

void loop() {
  unsigned long now = millis();
  if (now - ir_sensor_prev_time >= IR_SENSOR_PERIOD)
  {
    ir_sensor_prev_time = now;

    // 센서1 체크
    int current_yellow_state = digitalRead(YELLOW_IR_PIN);
    if (last_yellow_state == HIGH && current_yellow_state == LOW) {
      yellow_in_count++;
      digitalWrite(YELLOW_LED_PIN, HIGH);
    } else if (last_yellow_state == LOW && current_yellow_state == HIGH) {
      digitalWrite(YELLOW_LED_PIN, LOW);
    }
    last_yellow_state = current_yellow_state;

    // 센서2 체크
    int current_green_state = digitalRead(GREEN_IR_PIN);
    if (last_green_state == HIGH && current_green_state == LOW) {
      green_in_count++;
      digitalWrite(GREEN_LED_PIN, HIGH);
    } else if (last_green_state == LOW && current_green_state == HIGH) {
      digitalWrite(GREEN_LED_PIN, LOW);
    }
    last_green_state = current_green_state;
    
    // 센서3 체크
    int current_red_state = digitalRead(RED_IR_PIN);
    if (last_red_state == HIGH && current_red_state == LOW) {
      red_in_count++;
      digitalWrite(RED_LED_PIN, HIGH);
    } else if (last_red_state == LOW && current_red_state == HIGH) {
      digitalWrite(RED_LED_PIN, LOW);
    }
    last_red_state = current_red_state;

    // 센서4 체크
    int current_out_state = digitalRead(OUTPUT_IR_PIN);
    if (last_out_state == HIGH && current_out_state == LOW) {
      out_check_flag = true;
      out_total_count++;
    } else if (last_out_state == LOW && current_out_state == HIGH) {

    }
    last_out_state = current_out_state;

    // Serial.print("Y : ");
    // Serial.print(yellow_in_count);
    // Serial.print(", G : ");
    // Serial.print(green_in_count);
    // Serial.print(", R : ");
    // Serial.print(red_in_count);
    // Serial.print(", O : ");
    // Serial.println(out_total_count);
  }
  // 컬러센서 인식 부분
  // if (out_check_flag == true)
  // {
  //   digitalWrite(COLOR_SENSOR_LED_PIN, HIGH);
  //   if (now - color_sensor_prev_time >= COLOR_SENSOR_PERIOD)
  //   {
  //     color_sensor_prev_time = now;
  //     // Red Read
  //     digitalWrite(COLOR_SENSOR_S2_PIN, LOW);
  //     digitalWrite(COLOR_SENSOR_S3_PIN, LOW);
  //     red_frequency = pulseIn(COLOR_SENSOR_OUT_PIN, LOW);
  //     // Green Read
  //     digitalWrite(COLOR_SENSOR_S2_PIN, HIGH);
  //     digitalWrite(COLOR_SENSOR_S3_PIN, HIGH);
  //     green_frequency = pulseIn(COLOR_SENSOR_OUT_PIN, LOW);
  //     // Blue Read
  //     digitalWrite(COLOR_SENSOR_S2_PIN, LOW);
  //     digitalWrite(COLOR_SENSOR_S3_PIN, HIGH);
  //     blue_frequency = pulseIn(COLOR_SENSOR_OUT_PIN, LOW);
      
  //     Serial.print("R= ");
  //     Serial.print(red_frequency);
  //     Serial.print(" G= ");
  //     Serial.print(green_frequency);
  //     Serial.print(" B= ");
  //     Serial.println(blue_frequency);

  //     if (red_frequency < 20 && green_frequency < 26 && blue_frequency < 25) {
  //       result = 'R';
  //       red_in_count--;
  //       r_motor_flag = true;
  //     }
  //     else if (red_frequency > 25 && green_frequency < 26 && blue_frequency > 25) {
  //       result = 'G';
  //       green_in_count--;
  //       g_motor_flag = true;
  //     }
  //     else if (red_frequency < 20 && green_frequency < 20 && blue_frequency < 25) {
  //       result = 'Y';
  //       yellow_in_count--;
  //       y_motor_flag = true;
  //     }
  //     else {
  //       result = 'E';
  //     }
  //   }
  //   out_check_flag = false;
  // }

  // 시리얼 통신 부분
  int recv_size = 0;
  char recv_buffer[16];
  
  if (Serial.available() > 0)
  {
    recv_size = Serial.readBytesUntil('\n', recv_buffer,16);
  }
  if (recv_size > 0)
  {
    
    memset(cmd, 0x00, sizeof(cmd));
    memcpy(cmd, recv_buffer, 2);

    
    memset(send_buffer, 0x00, sizeof(send_buffer));
    memcpy(send_buffer, cmd, 2);
  }

  if(strncmp(cmd, "YC", 2)==0)
  {
    memset(send_buffer + 2, 0x00, 1);
    memcpy(send_buffer + 3, &yellow_in_count, 4);
    Serial.write(send_buffer, 7); 
  }
  else if (strncmp(cmd, "GC", 2)==0)
  {
    memset(send_buffer + 2, 0x00, 1);
    memcpy(send_buffer + 3, &green_in_count, 4);
    Serial.write(send_buffer, 7);
  }
  else if (strncmp(cmd, "RC", 2)==0)
  {
    memset(send_buffer + 2, 0x00, 1);
    memcpy(send_buffer + 3, &red_in_count, 4);
    Serial.write(send_buffer, 7);
  }
  else if (strncmp(cmd, "OC", 2)==0)
  {
    memset(send_buffer + 2, 0x00, 1);
    memcpy(send_buffer + 3, &out_total_count, 4);
    Serial.write(send_buffer, 7);
  }
  else if (strncmp(cmd, "YM", 2)==0)
  {
    y_motor_flag = true;
    memset(send_buffer + 2, 0x01, 1);
    memcpy(send_buffer + 3, 0x00, 4);
    Serial.write(send_buffer, 7);
  }
  else if (strncmp(cmd, "GM", 2)==0)
  {
    g_motor_flag = true;
    memset(send_buffer + 2, 0x01, 1);
    memcpy(send_buffer + 3, 0x00, 4);
    Serial.write(send_buffer, 7);
  }
  else if (strncmp(cmd, "RM", 2)==0)
  {
    r_motor_flag = true;
    memset(send_buffer + 2, 0x01, 1);
    memcpy(send_buffer + 3, 0x00, 4);
    Serial.write(send_buffer, 7);
  }
  // else if (strncmp(cmd, "CC", 2)==0)
  // {
  //   memset(send_buffer + 2, 0x01, 1);
  //   memcpy(send_buffer + 3, &result, 4);
  //   Serial.write(send_buffer, 7);
  // }
  else
  {

  }
  Serial.println();
  
  if (now - y_step_motor_prev_time >= STEP_MOTOR_PERIOD){
    y_step_motor_prev_time = now;
    if (y_motor_flag== true)
    {
      YellowStepper.step(-STEPS_PER_REVOLUTION);
    }
    y_motor_flag = false;
  }
  

  
  if (now - g_step_motor_prev_time >= STEP_MOTOR_PERIOD){
    g_step_motor_prev_time = now;
    if (g_motor_flag == true)
    {
      GreenStepper.step(-STEPS_PER_REVOLUTION);
    }
    g_motor_flag = false;
  }

  
  if (now - r_step_motor_prev_time >= STEP_MOTOR_PERIOD){
    r_step_motor_prev_time = now;
    if (r_motor_flag == true)
    {
      RedStepper.step(-STEPS_PER_REVOLUTION);
    }
    r_motor_flag = false;
  }
}
