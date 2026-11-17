#include "policy.h"

bool Policy::slot_ok(int n) { return n >= 1 && n <= 4; }

bool Policy::disk_ok(int d) { return d >= 1 && d <= 4; }

Status Policy::estop() {
  for (int i = 0; i < 4; ++i) {
    slot_[i] = false;
    disk_[i] = false;
  }
  return Status::Ok;
}

Status Policy::slot_on(int n) {
  if (!slot_ok(n)) return Status::BadArg;
  for (int i = 0; i < 4; ++i) {
    slot_[i] = false;
    disk_[i] = false;
  }
  slot_[n - 1] = true;
  return Status::Ok;
}

Status Policy::slot_off(int n) {
  if (!slot_ok(n)) return Status::BadArg;
  if (slot_[n - 1]) {
    slot_[n - 1] = false;
    for (int i = 0; i < 4; ++i) disk_[i] = false;
  }
  return Status::Ok;
}

Status Policy::disk_set(int n, int d, bool on) {
  if (!slot_ok(n) || !disk_ok(d)) return Status::BadArg;
  if (!slot_[n - 1]) return Status::SlotOff;
  disk_[d - 1] = on;
  return Status::Ok;
}

Status Policy::disk_on(int n, int d) { return disk_set(n, d, true); }

Status Policy::disk_off(int n, int d) { return disk_set(n, d, false); }

bool Policy::slot(int n) const {
  if (!slot_ok(n)) return false;
  return slot_[n - 1];
}

bool Policy::disk(int d) const {
  if (!disk_ok(d)) return false;
  return disk_[d - 1];
}

int Policy::active_slot() const {
  for (int i = 0; i < 4; ++i)
    if (slot_[i]) return i + 1;
  return 0;
}

uint8_t Policy::disk_mask() const {
  uint8_t mask = 0;
  for (int i = 0; i < 4; ++i)
    if (disk_[i]) mask |= static_cast<uint8_t>(1u << i);
  return mask;
}
