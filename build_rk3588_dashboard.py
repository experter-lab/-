"""Transplant Clinical Precision HTML/CSS from WSL snapshot into RK3588 dashboard.
Run once; outputs web_dashboard_node_rk3588_new.py for upload.
"""

with open('D:/A1/web_dashboard_node_snapshot.py', 'r', encoding='utf-8') as f:
    wsl = f.readlines()
with open('D:/A1/web_dashboard_node_rk3588.py', 'r', encoding='utf-8') as f:
    rk = f.readlines()


def find_line(lines, anchor, after=0):
    for i, l in enumerate(lines):
        if i < after:
            continue
        if anchor in l:
            return i
    return -1


wsl_link_start = find_line(wsl, '<link rel="preconnect" href="https://fonts.googleapis.com"')
wsl_style_end = find_line(wsl, '  </style>', wsl_link_start)
wsl_h1 = find_line(wsl, 'Medicine Delivery \xb7 Operator Console')
wsl_subtitle = find_line(wsl, 'RK3588 \xb7 ROS 2 Humble', wsl_h1)
wsl_task_status_start = find_line(wsl, '<span>用药清单</span><strong id="state_medication_progress">')
wsl_task_status_end = find_line(wsl, '</details>', wsl_task_status_start)
wsl_vision_start = find_line(wsl, '<span>识别来源</span><strong id="drug_source">')
wsl_vision_first_end = find_line(wsl, '</details>', wsl_vision_start)
wsl_vision_end = find_line(wsl, '</details>', wsl_vision_first_end + 1)
wsl_report_start = find_line(wsl, 'return `<!doctype html>', wsl_vision_end)
wsl_report_end = find_line(wsl, '</body></html>`;', wsl_report_start)

print('WSL anchors:', wsl_link_start, wsl_style_end, wsl_h1, wsl_subtitle,
      wsl_task_status_start, wsl_task_status_end, wsl_vision_start, wsl_vision_end,
      wsl_report_start, wsl_report_end)

rk_title = find_line(rk, '<title>智能送药小车任务面板</title>')
rk_style_open = find_line(rk, '  <style>', rk_title)
rk_style_end = find_line(rk, '  </style>', rk_style_open)
rk_h1 = find_line(rk, '<h1>智能送药小车任务面板</h1>')
rk_subtitle = find_line(rk, 'PC 端 ROS2 原型：创建送药任务', rk_h1)
rk_task_status_start = find_line(rk, '<span>用药清单</span><strong id="state_medication_progress">')
rk_task_status_progress_end = find_line(rk, '<span>进度</span><strong id="progress_text">', rk_task_status_start)
rk_vision_start = find_line(rk, '<span>识别来源</span><strong id="drug_source">')
rk_vision_stamp_end = find_line(rk, '<span>更新时间</span><strong id="drug_stamp">', rk_vision_start)
rk_report_start = find_line(rk, 'return `<!doctype html>')
rk_report_end = find_line(rk, '</body></html>`;', rk_report_start)

print('RK anchors:', rk_title, rk_style_open, rk_style_end, rk_h1, rk_subtitle,
      rk_task_status_start, rk_task_status_progress_end, rk_vision_start, rk_vision_stamp_end,
      rk_report_start, rk_report_end)

for k, v in [('wsl_link_start', wsl_link_start), ('wsl_style_end', wsl_style_end),
             ('wsl_h1', wsl_h1), ('wsl_subtitle', wsl_subtitle),
             ('wsl_task_status_start', wsl_task_status_start), ('wsl_task_status_end', wsl_task_status_end),
             ('wsl_vision_start', wsl_vision_start), ('wsl_vision_end', wsl_vision_end),
             ('wsl_report_start', wsl_report_start), ('wsl_report_end', wsl_report_end),
             ('rk_title', rk_title), ('rk_style_open', rk_style_open), ('rk_style_end', rk_style_end),
             ('rk_h1', rk_h1), ('rk_subtitle', rk_subtitle),
             ('rk_task_status_start', rk_task_status_start),
             ('rk_task_status_progress_end', rk_task_status_progress_end),
             ('rk_vision_start', rk_vision_start), ('rk_vision_stamp_end', rk_vision_stamp_end),
             ('rk_report_start', rk_report_start), ('rk_report_end', rk_report_end)]:
    if v < 0:
        raise SystemExit(f'anchor missing: {k}')

new_rk = []
new_rk.extend(rk[:rk_title + 1])
new_rk.extend(wsl[wsl_link_start:wsl_style_end + 1])
new_rk.extend(rk[rk_style_end + 1:rk_h1])
new_rk.extend(wsl[wsl_h1:wsl_subtitle + 1])
new_rk.extend(rk[rk_subtitle + 1:rk_task_status_start])
new_rk.extend(wsl[wsl_task_status_start:wsl_task_status_end + 1])
new_rk.extend(rk[rk_task_status_progress_end + 1:rk_vision_start])
new_rk.extend(wsl[wsl_vision_start:wsl_vision_end + 1])
new_rk.extend(rk[rk_vision_stamp_end + 1:rk_report_start])
new_rk.extend(wsl[wsl_report_start:wsl_report_end + 1])
new_rk.extend(rk[rk_report_end + 1:])

with open('D:/A1/web_dashboard_node_rk3588_new.py', 'w', encoding='utf-8', newline='') as f:
    f.writelines(new_rk)

print(f'Written {len(new_rk)} lines (orig RK3588 had {len(rk)})')
