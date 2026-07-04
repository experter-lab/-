#!/usr/bin/env python3
"""给 sllidar_node.cpp 添加 range_max_filter 参数支持"""
import sys
from pathlib import Path

src = Path(sys.argv[1])
text = src.read_text(encoding="utf-8")

# 1) declare_parameter (在 scan_frequency declare 后)
old1 = 'this->declare_parameter<float>("scan_frequency",10);'
new1 = 'this->declare_parameter<float>("scan_frequency",10);\n        this->declare_parameter<float>("range_max_filter", 0.0);'
assert old1 in text, "patch1 anchor not found"
text = text.replace(old1, new1, 1)

# 2) get_parameter_or — 在 scan_frequency get 后追加 range_max_filter
old2 = '            this->get_parameter_or<float>("scan_frequency", scan_frequency, 10.0);'
new2 = old2 + '\n        }\n        this->get_parameter_or<float>("range_max_filter", range_max_filter, 0.0f);\n        if (false) {'
# 用上面这种结构会破坏后续花括号，换简单方案：在所有 init_param 末尾追加。
# 这里改回简单方案：在 scan_frequency 那行的 if/else 块之后追加。
text = text.replace(new2, old2)  # 撤回

# 改为：找到 init_param 函数末尾 `}` 前追加
init_param_end_marker = '    void init_param()'
idx = text.find(init_param_end_marker)
assert idx >= 0
# 找到 init_param 函数的结束 }
brace_open = text.find('{', idx)
depth = 0
i = brace_open
while i < len(text):
    if text[i] == '{':
        depth += 1
    elif text[i] == '}':
        depth -= 1
        if depth == 0:
            break
    i += 1
assert depth == 0, "could not find init_param closing brace"
insert_pt = i  # 闭合 } 的位置
inject = '        this->get_parameter_or<float>("range_max_filter", range_max_filter, 0.0f);\n    '
text = text[:insert_pt] + inject + text[insert_pt:]

# 3) 添加 member 变量
old3 = '    float scan_frequency;'
new3 = '    float scan_frequency;\n    float range_max_filter = 0.0;'
assert old3 in text, "patch3 anchor not found"
text = text.replace(old3, new3, 1)

# 4) 在 work_loop 里截断 max_distance
old4 = '            max_distance = (float)current_scan_mode.max_distance;'
new4 = (
    '            max_distance = (float)current_scan_mode.max_distance;\n'
    '            if (range_max_filter > 0.0f && range_max_filter < max_distance) {\n'
    '                RCLCPP_INFO(this->get_logger(), "range_max_filter active: clipping max_distance from %.1f to %.1f", max_distance, range_max_filter);\n'
    '                max_distance = range_max_filter;\n'
    '            }'
)
assert old4 in text, "patch4 anchor not found"
text = text.replace(old4, new4, 1)

# 5) publish_scan: 单点距离裁剪 (两个 for 循环)
old5a = '''            for (size_t i = 0; i < node_count; i++) {
                float read_value = (float) nodes[i].dist_mm_q2/4.0f/1000;
                if (read_value == 0.0)
                    scan_msg->ranges[i] = std::numeric_limits<float>::infinity();
                else
                    scan_msg->ranges[i] = read_value;
                scan_msg->intensities[i] = (float) (nodes[i].quality >> 2);
            }'''
new5a = '''            for (size_t i = 0; i < node_count; i++) {
                float read_value = (float) nodes[i].dist_mm_q2/4.0f/1000;
                if (read_value == 0.0 || read_value > max_distance)
                    scan_msg->ranges[i] = std::numeric_limits<float>::infinity();
                else
                    scan_msg->ranges[i] = read_value;
                scan_msg->intensities[i] = (float) (nodes[i].quality >> 2);
            }'''
assert old5a in text, "patch5a anchor not found"
text = text.replace(old5a, new5a, 1)

old5b = '''            for (size_t i = 0; i < node_count; i++) {
                float read_value = (float)nodes[i].dist_mm_q2/4.0f/1000;
                if (read_value == 0.0)
                    scan_msg->ranges[node_count-1-i] = std::numeric_limits<float>::infinity();
                else
                    scan_msg->ranges[node_count-1-i] = read_value;
                scan_msg->intensities[node_count-1-i] = (float) (nodes[i].quality >> 2);
            }'''
new5b = '''            for (size_t i = 0; i < node_count; i++) {
                float read_value = (float)nodes[i].dist_mm_q2/4.0f/1000;
                if (read_value == 0.0 || read_value > max_distance)
                    scan_msg->ranges[node_count-1-i] = std::numeric_limits<float>::infinity();
                else
                    scan_msg->ranges[node_count-1-i] = read_value;
                scan_msg->intensities[node_count-1-i] = (float) (nodes[i].quality >> 2);
            }'''
assert old5b in text, "patch5b anchor not found"
text = text.replace(old5b, new5b, 1)

src.write_text(text, encoding="utf-8")
print("✅ Patched 5 locations successfully")
