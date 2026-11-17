#include "policy.h"

#include <cstdio>

static int fails = 0;

static void expect(bool cond, const char* msg) {
  if (!cond) {
    std::printf("FAIL %s\n", msg);
    ++fails;
  }
}

static bool all_off(const Policy& p) {
  for (int i = 1; i <= 4; ++i)
    if (p.slot(i) || p.disk(i)) return false;
  return true;
}

static bool only_slot(const Policy& p, int n) {
  for (int i = 1; i <= 4; ++i) {
    if (p.slot(i) != (i == n)) return false;
  }
  return true;
}

static bool disks_clear(const Policy& p) {
  for (int d = 1; d <= 4; ++d)
    if (p.disk(d)) return false;
  return true;
}

int main() {
  {
    Policy p;
    expect(p.slot_on(1) == Status::Ok, "slot 1 on");
    expect(p.disk_on(1, 1) == Status::Ok, "disk 1");
    expect(p.disk_on(1, 2) == Status::Ok, "disk 2");
    expect(p.slot_on(2) == Status::Ok, "slot 2 on");
    expect(only_slot(p, 2), "slot 2 forces slot 1 off");
    expect(disks_clear(p), "slot 2 clears disks");
    expect(p.disk_on(1, 1) == Status::SlotOff, "disk on the slot that just went off");
    expect(disks_clear(p), "rejected disk leaves disks clear");
    expect(only_slot(p, 2), "rejected disk leaves slot 2");
  }

  {
    Policy p;
    expect(p.disk_on(2, 1) == Status::SlotOff, "disk while slot off");
    expect(p.disk_off(2, 1) == Status::SlotOff, "disk off while slot off");
    expect(all_off(p), "disk while off does not change state");
  }

  {
    Policy p;
    expect(p.slot_on(1) == Status::Ok, "prep slot");
    expect(p.disk_on(1, 3) == Status::Ok, "prep disk");
    expect(p.disk_on(2, 1) == Status::SlotOff, "other slot disk");
    expect(only_slot(p, 1), "other slot disk keeps slot 1");
    expect(p.disk(3) && !p.disk(1), "other slot disk keeps disks");
  }

  {
    Policy p;
    expect(p.slot_on(1) == Status::Ok, "estop prep slot");
    expect(p.disk_on(1, 4) == Status::Ok, "estop prep disk");
    expect(p.slot_on(3) == Status::Ok, "estop prep slot 3");
    expect(p.disk_on(3, 2) == Status::Ok, "estop prep disk 2");
    expect(p.estop() == Status::Ok, "estop");
    expect(all_off(p), "estop clears all");
  }

  {
    Policy p;
    expect(p.slot_on(1) == Status::Ok, "bad prep");
    expect(p.disk_on(1, 1) == Status::Ok, "bad prep disk");
    expect(p.slot_on(0) == Status::BadArg, "n=0");
    expect(p.slot_on(5) == Status::BadArg, "n=5");
    expect(p.slot_off(0) == Status::BadArg, "off n=0");
    expect(p.slot_off(5) == Status::BadArg, "off n=5");
    expect(p.disk_on(0, 1) == Status::BadArg, "disk n=0");
    expect(p.disk_on(5, 1) == Status::BadArg, "disk n=5");
    expect(p.disk_on(1, 0) == Status::BadArg, "d=0");
    expect(p.disk_on(1, 5) == Status::BadArg, "d=5");
    expect(only_slot(p, 1), "bad args keep slot");
    expect(p.disk(1) && !p.disk(2), "bad args keep disk");
  }

  if (fails) {
    std::printf("%d failed\n", fails);
    return 1;
  }
  std::printf("ok\n");
  return 0;
}
