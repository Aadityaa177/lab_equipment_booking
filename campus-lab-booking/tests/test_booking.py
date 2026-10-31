# Manual integration checks after seeding:
# 1. Sign in STU001 / DemoPass123! and book exactly one computer.
# 2. Sign in FAC001 / DemoPass123! and book two computers.
# 3. Confirm overlapping booking attempts return HTTP 409.
# 4. Confirm PC-03 (unhealthy) is not available.
# 5. Staff can view health but cannot update it.
# 6. In-charge can update assigned lab computers.
