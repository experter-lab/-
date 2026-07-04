#!/usr/bin/env bash
# Nav2 yaml 调参: robot_radius → footprint, inflation 调小, scaling 衰减更平滑
set -euo pipefail
YAML=/mnt/sdcard/medicine_robot_data/config/rk3588_nav2_params.yaml
BAK="${YAML}.bak.$(date +%Y%m%d_%H%M%S)"

cp "$YAML" "$BAK"
echo "==> 备份: $BAK"

# local_costmap (在 'local_costmap:' 开头到 'local_costmap_client:' 之间)
# 不容易用 sed 安全做 section-scoped 修改,用 awk 配合上下文判断

python3 <<'PYEOF'
import re

path = "/mnt/sdcard/medicine_robot_data/config/rk3588_nav2_params.yaml"
with open(path) as f:
    s = f.read()

# 矩形 footprint (车体 44cm长 x 36cm宽,中心在 base_link)
FOOTPRINT = '      footprint: "[[0.22, 0.18], [0.22, -0.18], [-0.22, -0.18], [-0.22, 0.18]]"'

# 替换 local_costmap 段
def patch(content, header_marker, end_marker, new_inflation, new_scaling):
    """在 header_marker 到 end_marker 之间替换 robot_radius/inflation/scaling"""
    i = content.index(header_marker)
    j = content.index(end_marker, i)
    section = content[i:j]
    # robot_radius → footprint
    section = re.sub(r'(\s*)robot_radius:\s*[\d.]+',
                     '\n' + FOOTPRINT, section, count=1)
    # inflation_radius
    section = re.sub(r'inflation_radius:\s*[\d.]+',
                     f'inflation_radius: {new_inflation}', section)
    # cost_scaling_factor
    section = re.sub(r'cost_scaling_factor:\s*[\d.]+',
                     f'cost_scaling_factor: {new_scaling}', section)
    return content[:i] + section + content[j:]

s = patch(s, 'local_costmap:\n  local_costmap:',
          'local_costmap_client:', new_inflation=0.22, new_scaling=3.0)
s = patch(s, 'global_costmap:\n  global_costmap:',
          'global_costmap_client:', new_inflation=0.30, new_scaling=3.0)

with open(path, 'w') as f:
    f.write(s)
print("==> 改完")
PYEOF

echo
echo "==> 改后的 footprint/inflation 行:"
grep -nE 'footprint:|robot_radius:|inflation_radius:|cost_scaling_factor:' "$YAML"
