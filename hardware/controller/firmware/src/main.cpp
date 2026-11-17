#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>

#include <cstdio>
#include <cstring>

#include "policy.h"

#if __has_include("secrets.h")
#include "secrets.h"
#endif

#ifndef WIFI_ENABLED
#define WIFI_ENABLED 0
#endif

// PRESENT_N: плата на месте замыкает на землю. Высокий уровень — слота нет.
// PCA9554 после питания держит все ножки входами. Сначала регистр выхода в 0,
// потом IO0..IO3 на выход, иначе мотор дёрнется.

static const int SLOT_GPIO[4] = {25, 26, 27, 14};
static const int PRESENT_GPIO[4] = {34, 35, 36, 39};
static const int PIN_SDA = 21;
static const int PIN_SCL = 22;
static const int PIN_RST = 13;
static const int PIN_LED = 32;
static const uint8_t TCA_ADDR = 0x70;
static const uint8_t EEPROM_ADDR = 0x50;
static const uint8_t PCA_ADDR = 0x20;
static const uint8_t PCA_OUT = 0x01;
static const uint8_t PCA_CFG = 0x03;
static const uint8_t PCA_CFG_DISKS = 0xF0;

static Policy policy;
static char line[80];
static int line_n = 0;
static uint32_t led_ms = 0;
static bool led_on = false;

#if WIFI_ENABLED
static WiFiServer server(2323);
static WiFiClient client;
static char wifi_line[80];
static int wifi_n = 0;
#endif

enum class From { Uart, Wifi };

static void reply(From from, const char* text) {
  if (from == From::Uart) {
    Serial.print(text);
    Serial.print('\n');
  }
#if WIFI_ENABLED
  if (from == From::Wifi && client.connected()) {
    client.print(text);
    client.print('\n');
  }
#else
  (void)from;
#endif
}

static void slots_low() {
  for (int i = 0; i < 4; ++i) digitalWrite(SLOT_GPIO[i], LOW);
}

static bool tca_select(int channel) {
  Wire.beginTransmission(TCA_ADDR);
  Wire.write(static_cast<uint8_t>(1u << channel));
  return Wire.endTransmission() == 0;
}

static bool pca_write(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(PCA_ADDR);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

// mask: бит 0 — диск 1. Конфигурация после регистра выхода.
static bool pca_apply(int slot, uint8_t mask) {
  if (!tca_select(slot - 1)) return false;
  delay(1);
  if (!pca_write(PCA_OUT, mask)) return false;
  if (!pca_write(PCA_CFG, PCA_CFG_DISKS)) return false;
  return true;
}

static void slot_power(int slot, bool on) {
  digitalWrite(SLOT_GPIO[slot - 1], on ? HIGH : LOW);
}

// До 300 мс после 12 В. NACK адреса — нет EEPROM. Иной сбой шины — i2c.
static bool wait_eeprom(int slot, const char** err) {
  uint32_t t0 = millis();
  bool saw_nack = false;
  while (static_cast<uint32_t>(millis() - t0) < 300) {
    if (!tca_select(slot - 1)) {
      *err = "ERR i2c fail";
      return false;
    }
    Wire.beginTransmission(EEPROM_ADDR);
    Wire.write(0x00);
    uint8_t rc = Wire.endTransmission(false);
    if (rc == 0 && Wire.requestFrom(static_cast<int>(EEPROM_ADDR), 4) == 4) {
      char magic[4];
      for (int i = 0; i < 4; ++i) magic[i] = static_cast<char>(Wire.read());
      if (magic[0] == 'S' && magic[1] == 'L' && magic[2] == 'I' && magic[3] == 'B') return true;
      *err = "ERR no_eeprom magic";
      return false;
    }
    if (rc == 2 || rc == 3) saw_nack = true;
    else if (rc != 0) {
      *err = "ERR i2c fail";
      return false;
    }
    delay(20);
  }
  *err = saw_nack ? "ERR no_eeprom magic" : "ERR i2c fail";
  return false;
}

static void fail_slot(int slot) {
  slot_power(slot, false);
  policy.slot_off(slot);
}

static bool parse_num(const char* s, int* out) {
  if (s == nullptr || *s == '\0') return false;
  int v = 0;
  for (const char* p = s; *p; ++p) {
    if (*p < '0' || *p > '9') return false;
    v = v * 10 + (*p - '0');
  }
  *out = v;
  return true;
}

static int split(char* s, char** tok, int cap) {
  int n = 0;
  while (*s && n < cap) {
    while (*s == ' ') ++s;
    if (*s == '\0') break;
    tok[n++] = s;
    while (*s && *s != ' ') ++s;
    if (*s) *s++ = '\0';
  }
  return n;
}

static void send_state(From from) {
  char buf[80];
  std::snprintf(
      buf, sizeof(buf), "OK state slots=%d,%d,%d,%d present=%d,%d,%d,%d disks=%d,%d,%d,%d",
      policy.slot(1), policy.slot(2), policy.slot(3), policy.slot(4),
      digitalRead(PRESENT_GPIO[0]) == LOW, digitalRead(PRESENT_GPIO[1]) == LOW,
      digitalRead(PRESENT_GPIO[2]) == LOW, digitalRead(PRESENT_GPIO[3]) == LOW,
      policy.disk(1), policy.disk(2), policy.disk(3), policy.disk(4));
  reply(from, buf);
}

static void on_slot(From from, int n, bool on) {
  if (n < 1 || n > 4) {
    reply(from, "ERR bad_arg range");
    return;
  }
  if (!on) {
    int prev = policy.active_slot();
    if (prev == n) pca_apply(n, 0);
    policy.slot_off(n);
    slot_power(n, false);
    char buf[32];
    std::snprintf(buf, sizeof(buf), "OK slot %d off", n);
    reply(from, buf);
    return;
  }
  if (digitalRead(PRESENT_GPIO[n - 1]) == HIGH) {
    reply(from, "ERR not_present absent");
    return;
  }
  int prev = policy.active_slot();
  if (prev && prev != n) pca_apply(prev, 0);
  slots_low();
  policy.slot_on(n);
  slot_power(n, true);
  const char* err = "ERR i2c fail";
  if (!wait_eeprom(n, &err)) {
    fail_slot(n);
    reply(from, err);
    return;
  }
  if (!pca_apply(n, 0)) {
    fail_slot(n);
    reply(from, "ERR i2c fail");
    return;
  }
  char buf[32];
  std::snprintf(buf, sizeof(buf), "OK slot %d on", n);
  reply(from, buf);
}

static void on_disk(From from, int n, int d, bool on) {
  Status st = on ? policy.disk_on(n, d) : policy.disk_off(n, d);
  if (st == Status::BadArg) {
    reply(from, "ERR bad_arg range");
    return;
  }
  if (st == Status::SlotOff) {
    reply(from, "ERR slot_off off");
    return;
  }
  if (!pca_apply(n, policy.disk_mask())) {
    if (on) policy.disk_off(n, d);
    else policy.disk_on(n, d);
    reply(from, "ERR i2c fail");
    return;
  }
  char buf[32];
  std::snprintf(buf, sizeof(buf), "OK disk %d %d %s", n, d, on ? "on" : "off");
  reply(from, buf);
}

static void handle(From from, char* text) {
  char* tok[6];
  int n = split(text, tok, 6);
  if (n == 0) return;
  if (n == 1 && std::strcmp(tok[0], "PING") == 0) {
    reply(from, "OK pong");
    return;
  }
  if (n == 1 && std::strcmp(tok[0], "ESTOP") == 0) {
    int prev = policy.active_slot();
    if (prev) pca_apply(prev, 0);
    policy.estop();
    slots_low();
    reply(from, "OK estop");
    return;
  }
  if (n == 1 && std::strcmp(tok[0], "STATE") == 0) {
    send_state(from);
    return;
  }
  if (n == 3 && std::strcmp(tok[0], "SLOT") == 0) {
    int slot = 0;
    if (!parse_num(tok[1], &slot)) {
      reply(from, "ERR bad_arg range");
      return;
    }
    if (std::strcmp(tok[2], "ON") == 0) on_slot(from, slot, true);
    else if (std::strcmp(tok[2], "OFF") == 0) on_slot(from, slot, false);
    else reply(from, "ERR bad_arg command");
    return;
  }
  if (n == 4 && std::strcmp(tok[0], "DISK") == 0) {
    int slot = 0;
    int disk = 0;
    if (!parse_num(tok[1], &slot) || !parse_num(tok[2], &disk)) {
      reply(from, "ERR bad_arg range");
      return;
    }
    if (std::strcmp(tok[3], "ON") == 0) on_disk(from, slot, disk, true);
    else if (std::strcmp(tok[3], "OFF") == 0) on_disk(from, slot, disk, false);
    else reply(from, "ERR bad_arg command");
    return;
  }
  reply(from, "ERR bad_arg command");
}

static void push_char(From from, char* buf, int* len, int cap, char c) {
  if (c == '\r') return;
  if (c == '\n') {
    buf[*len] = '\0';
    handle(from, buf);
    *len = 0;
    return;
  }
  if (*len + 1 >= cap) {
    *len = 0;
    reply(from, "ERR bad_arg command");
    return;
  }
  buf[(*len)++] = c;
}

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(100000);

  pinMode(PIN_RST, OUTPUT);
  digitalWrite(PIN_RST, LOW);
  delay(1);
  digitalWrite(PIN_RST, HIGH);

  for (int i = 0; i < 4; ++i) {
    pinMode(SLOT_GPIO[i], OUTPUT);
    digitalWrite(SLOT_GPIO[i], LOW);
    pinMode(PRESENT_GPIO[i], INPUT);
  }
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  WiFi.mode(WIFI_OFF);
#if WIFI_ENABLED
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  server.begin();
#endif
}

void loop() {
  while (Serial.available()) {
    push_char(From::Uart, line, &line_n, static_cast<int>(sizeof(line)),
              static_cast<char>(Serial.read()));
  }

#if WIFI_ENABLED
  if (!client.connected()) {
    client = server.available();
    wifi_n = 0;
  } else {
    while (client.available()) {
      push_char(From::Wifi, wifi_line, &wifi_n, static_cast<int>(sizeof(wifi_line)),
                static_cast<char>(client.read()));
    }
  }
#endif

  uint32_t now = millis();
  if (static_cast<uint32_t>(now - led_ms) >= 500) {
    led_ms = now;
    led_on = !led_on;
    digitalWrite(PIN_LED, led_on ? HIGH : LOW);
  }
}
