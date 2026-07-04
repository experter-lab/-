# Terminal command pitfalls

## 2026-06-16: PowerShell + plink remote bash quoting

Context:

- Local workspace shell is PowerShell.
- RK3588 access uses PuTTY: `D:\Program Files\PuTTY\plink.exe`.
- Board target used in this session: `192.168.31.125`.

Pitfall:

- Do not put remote bash variables inside a local PowerShell double-quoted command.
- PowerShell expands `$node`, `$n`, `$t`, etc. locally before `plink` sends the command.
- This caused remote lifecycle commands to lose the node name, producing blank labels like `CONFIG:` and misleading `Node not found` output.
- Remote pipelines with regex alternation such as `grep -E 'a|b|c'` are also fragile when nested in the wrong quotes.

Correct pattern for remote loops or multiline scripts:

```powershell
@'
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
for node in bt_navigator behavior_server waypoint_follower velocity_smoother; do
  echo "NODE:$node"
  ros2 lifecycle get "/$node" || true
done
'@ | & 'D:\Program Files\PuTTY\plink.exe' -batch -ssh elf@192.168.31.125 -pw <password> "bash -s"
```

Rules:

- Use a PowerShell single-quoted here-string (`@' ... '@`) piped to `plink ... "bash -s"` for remote variables, loops, pipes, and multiline logic.
- Use a simple locally single-quoted one-liner only when no remote variables or complex quoting are needed.
- Do not record the real password in memory files.

## 2026-06-16: Old Codex conversation logs are context, not live state

Useful logs:

- `C:\Users\cgz\.codex\history.jsonl`
- `C:\Users\cgz\.codex\session_index.jsonl`
- Session id found in this recovery: `019eaf60-d80a-76b0-985d-c0c7d29abb58`
- Session title: `排查严重问题`

Rule:

- Recovered conversation logs can explain what the user was doing, but they do not prove current board state.
- Always verify current reachability and ROS state before acting.

Quick check:

```powershell
Test-Connection 192.168.31.125 -Count 2 -Quiet
```

Then inspect live board state with `ps`, ROS topics, lifecycle states, and action info.

## 2026-06-16: Long RK3588 scripts can outlive SSH timeout

Pitfall:

- `NAV2_ENABLE_DRIVE=0 bash /mnt/sdcard/rk3588_start_nav2_carto.sh` can continue running on the RK3588 after the local `plink` call times out.
- A local timeout means "unknown", not automatically "failed".

Follow-up checks:

```bash
ps -ef | grep -E 'rf2o|rk3588_guarded_odom|ekf_node|cartographer|static_map_server|navigation_launch'
tail -n 80 /tmp/rk3588_odom_fusion.log
tail -n 120 /tmp/rk3588_carto_localization.log
tail -n 120 /tmp/rk3588_nav2_carto_navigation.log
ros2 action info /navigate_to_pose
```

Safety rule:

- Before starting or recovering Nav2, run `rk3588_safe_stop.sh` and verify `BRAKE_STATUS_SAFE`.
- Keep `NAV2_ENABLE_DRIVE=0` during bring-up.
- Do not authorize the chassis until localization, action server, lifecycle state, and RViz/Web alignment are all rechecked.

## 2026-06-17: PowerShell here-strings can inject CRLF into remote bash

Pitfall:

- A PowerShell here-string piped directly to `plink ... "bash -s"` can preserve `\r`.
- Remote bash commands then receive arguments like `220\r`, which broke:

```bash
head -n 220
```

with:

```text
head: invalid number of lines: "220\r"
```

- Another bad variant was accidentally sending PowerShell syntax (`$null`) to remote bash, causing:

```text
bash: $null: ambiguous redirect
```

Correct pattern:

```powershell
@'
remote bash commands here
'@ | & 'D:\Program Files\PuTTY\plink.exe' -batch -ssh elf@192.168.31.125 -pw <password> "tr -d '\r' | bash -s"
```

Rules:

- Use `tr -d '\r' | bash -s` for multiline scripts sent from PowerShell to RK3588.
- Keep remote scripts pure bash; do not use PowerShell-only syntax such as `$null`.
- For line-limited output, prefer `sed -n '1,220p'` on the remote side if CRLF risk is possible.

## 2026-06-17: PuTTY plink must include the RK3588 username

Pitfall:

- `plink -batch -pw elf 192.168.31.125 "echo SSH_OK"` can exit quickly with no stdout.
- With `-v`, the real reason is:

```text
No username provided
```

Correct pattern:

```powershell
plink -batch -pw elf elf@192.168.31.125 "echo SSH_OK"
```

For multiline remote bash:

```powershell
@'
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
remote bash commands here
'@ | & 'D:\Program Files\PuTTY\plink.exe' -batch -ssh elf@192.168.31.125 -pw elf "tr -d '\r' | bash -s"
```

## 2026-06-17: Do not enable bash nounset before ROS setup files

Pitfall:

- A remote script with `set -u` before sourcing ROS setup can fail immediately:

```text
/opt/ros/humble/setup.bash: line 8: AMENT_TRACE_SETUP_FILES: unbound variable
```

Rule:

- Source ROS first, then use stricter bash options only after setup if needed.
- Prefer avoiding `set -u` in quick RK3588 ROS probe scripts.

## 2026-06-17: Use rg -g patterns in PowerShell, not globbed path arguments

Pitfall:

- This is invalid in PowerShell for `rg` path arguments:

```powershell
rg -n "backup" D:\A1\rk3588_* D:\A1\*.sh
```

- It can fail with:

```text
The filename, directory name, or volume label syntax is incorrect. (os error 123)
```

Correct pattern:

```powershell
rg -n -g "rk3588_*.sh" -g "*.sh" "backup|authorize_control" D:\A1
```
