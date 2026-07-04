#!/usr/bin/env python3
from pathlib import Path
import shutil
import time


ROOT = Path("/mnt/sdcard/medicine_robot_ws")
UPLOAD = Path("/tmp/m2_voice_opt_20260609")
BACKUP = ROOT / "backups" / f"m2_voice_opt_{time.strftime('%Y%m%d_%H%M%S')}"


def read_text(path):
    return path.read_text(encoding="utf-8")


def write_text(path, text):
    path.write_text(text, encoding="utf-8")


def backup_file(path):
    rel = path.relative_to(ROOT)
    dst = BACKUP / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    return dst


def copy_uploaded(src_rel, dst_rel):
    src = UPLOAD / src_rel
    dst = ROOT / dst_rel
    if not src.exists():
        raise FileNotFoundError(f"uploaded file missing: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        backup_file(dst)
    shutil.copy2(src, dst)
    print(f"copied {src_rel} -> {dst_rel}")


def patch_bringup_launch():
    path = ROOT / "src/medicine_robot_bringup/launch/pc_delivery_demo.launch.py"
    backup_file(path)
    text = read_text(path)
    marker = '    default_aikit_sdk_dir = os.environ.get("AIKIT_SDK_DIR", "/home/cgz/medicine_robot_ws/aikit_sdk")\n'
    if marker not in text:
        old = '    stations_file = get_package_share_directory("medicine_task_manager") + "/config/stations.yaml"\n'
        if old not in text:
            raise RuntimeError("bringup launch stations_file insertion point not found")
        text = text.replace(old, old + marker, 1)
    old_arg = '        DeclareLaunchArgument("aikit_sdk_dir", default_value="/home/cgz/medicine_robot_ws/aikit_sdk"),\n'
    new_arg = '        DeclareLaunchArgument("aikit_sdk_dir", default_value=default_aikit_sdk_dir),\n'
    if old_arg in text:
        text = text.replace(old_arg, new_arg, 1)
    elif new_arg not in text:
        raise RuntimeError("bringup launch aikit_sdk_dir argument not found")
    old_pulse = '        DeclareLaunchArgument("pulse_server", default_value="unix:/mnt/wslg/PulseServer"),\n'
    new_pulse = '        DeclareLaunchArgument("pulse_server", default_value=os.environ.get("PULSE_SERVER", "")),\n'
    if old_pulse in text:
        text = text.replace(old_pulse, new_pulse, 1)
    elif new_pulse not in text:
        raise RuntimeError("bringup launch pulse_server argument not found")
    write_text(path, text)
    print("patched medicine_robot_bringup launch")


def patch_bringup_package():
    path = ROOT / "src/medicine_robot_bringup/package.xml"
    backup_file(path)
    text = read_text(path)
    old = "  <exec_depend>wheeltec_aikit_esr</exec_depend>\n"
    new = "  <!-- wheeltec_aikit_esr is optional and guarded by enable_aikit_esr. -->\n"
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise RuntimeError("bringup package wheeltec_aikit_esr dependency not found")
    write_text(path, text)
    print("patched medicine_robot_bringup package.xml")


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    copy_uploaded(
        "medicine_voice_interaction/package.xml",
        "src/medicine_voice_interaction/package.xml",
    )
    copy_uploaded(
        "medicine_voice_interaction/setup.py",
        "src/medicine_voice_interaction/setup.py",
    )
    copy_uploaded(
        "medicine_voice_interaction/setup.cfg",
        "src/medicine_voice_interaction/setup.cfg",
    )
    copy_uploaded(
        "medicine_voice_interaction/resource/medicine_voice_interaction",
        "src/medicine_voice_interaction/resource/medicine_voice_interaction",
    )
    copy_uploaded(
        "medicine_voice_interaction/medicine_voice_interaction/__init__.py",
        "src/medicine_voice_interaction/medicine_voice_interaction/__init__.py",
    )
    copy_uploaded(
        "medicine_voice_interaction/medicine_voice_interaction/voice_console_node.py",
        "src/medicine_voice_interaction/medicine_voice_interaction/voice_console_node.py",
    )
    copy_uploaded(
        "medicine_voice_interaction/medicine_voice_interaction/m2_voice_bridge_node.py",
        "src/medicine_voice_interaction/medicine_voice_interaction/m2_voice_bridge_node.py",
    )
    copy_uploaded(
        "medicine_voice_interaction/medicine_voice_interaction/voice_command_dispatcher_node.py",
        "src/medicine_voice_interaction/medicine_voice_interaction/voice_command_dispatcher_node.py",
    )
    patch_bringup_launch()
    patch_bringup_package()
    print(f"backup_dir={BACKUP}")


if __name__ == "__main__":
    main()
