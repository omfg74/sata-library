#pragma once

#include <cstdint>

// Правила из hardware/INTERFACE.md. Без Arduino, чтобы гнать тест на хосте.

enum class Status { Ok, BadArg, SlotOff };

class Policy {
 public:
  Status estop();
  Status slot_on(int n);
  Status slot_off(int n);
  Status disk_on(int n, int d);
  Status disk_off(int n, int d);

  bool slot(int n) const;
  bool disk(int d) const;
  int active_slot() const;
  uint8_t disk_mask() const;

 private:
  bool slot_[4]{};
  bool disk_[4]{};

  Status disk_set(int n, int d, bool on);
  static bool slot_ok(int n);
  static bool disk_ok(int d);
};
