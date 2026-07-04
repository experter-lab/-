#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库集成脚本 - 自动将数据库功能集成到 web_dashboard_node.py
"""

import re
import sys
import os

def integrate_database(file_path):
    print(f"正在读取文件: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经集成
    if 'from delivery_database import DeliveryDatabase' in content:
        print("✓ 数据库已经集成，无需重复操作")
        return False

    # 1. 在 import 区域添加数据库导入
    import_pattern = r'(from std_msgs.msg import String)'
    import_replacement = r'\1\n\ntry:\n    from delivery_database import DeliveryDatabase\n    DB_AVAILABLE = True\nexcept ImportError:\n    DB_AVAILABLE = False\n    print("Warning: delivery_database not available")'

    content = re.sub(import_pattern, import_replacement, content, count=1)

    # 2. 在 __init__ 方法中初始化数据库
    # 查找 super().__init__ 后面添加数据库初始化
    init_pattern = r"(super\(\).__init__\('medicine_web_dashboard'\))"

    db_init_code = r'''\1

        # 初始化数据库
        self.db = None
        if DB_AVAILABLE:
            try:
                self.db = DeliveryDatabase()
                self.get_logger().info('✓ 数据库初始化成功')
            except Exception as e:
                self.get_logger().error(f'数据库初始化失败: {e}')
                self.db = None
        else:
            self.get_logger().warn('数据库模块不可用，数据不会持久化')'''

    content = re.sub(init_pattern, db_init_code, content, count=1)

    # 3. 添加数据库保存方法（在 main 函数之前）
    save_methods = '''
    def _save_batch_to_db(self, batch_data):
        """保存批次到数据库"""
        if self.db is None:
            return
        try:
            self.db.save_batch(batch_data)
            self.get_logger().info(f"✓ 批次 {batch_data.get('batch_id')} 已保存到数据库")
        except Exception as e:
            self.get_logger().error(f"保存批次失败: {e}")

    def _save_scan_to_db(self, batch_id, stage, scan_data, result):
        """保存扫码记录到数据库"""
        if self.db is None:
            return
        try:
            self.db.save_scan_record(
                batch_id=batch_id,
                stage=stage,
                product_code=scan_data.get('product_code', ''),
                trace_id=scan_data.get('trace_id', ''),
                result=result,
                patient_id=scan_data.get('patient_id'),
                patient_name=scan_data.get('patient_name'),
                medication_name=scan_data.get('medication_name'),
                expected_product_code=scan_data.get('expected_product_code'),
                expected_trace_id=scan_data.get('expected_trace_id'),
                operator=scan_data.get('operator', 'system'),
                station=scan_data.get('station')
            )
            self.get_logger().info(f"✓ 扫码记录已保存: {stage} - {result}")
        except Exception as e:
            self.get_logger().error(f"保存扫码记录失败: {e}")

    def _save_exception_to_db(self, batch_id, exception_type, description, **kwargs):
        """保存异常记录到数据库"""
        if self.db is None:
            return
        try:
            self.db.save_exception(
                batch_id=batch_id,
                exception_type=exception_type,
                description=description,
                patient_id=kwargs.get('patient_id'),
                medication_id=kwargs.get('medication_id'),
                station=kwargs.get('station')
            )
            self.get_logger().info(f"✓ 异常记录已保存: {exception_type}")
        except Exception as e:
            self.get_logger().error(f"保存异常记录失败: {e}")

'''

    # 在 main 函数之前添加这些方法
    main_pattern = r'(def main\(args=None\):)'
    content = re.sub(main_pattern, save_methods + r'\1', content, count=1)

    # 备份原文件
    backup_path = file_path + '.backup_' + str(int(os.path.getmtime(file_path)))
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已创建备份: {backup_path}")

    # 写入修改后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 数据库集成完成")
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = '/mnt/sdcard/medicine_robot_ws/src/medicine_web_dashboard/medicine_web_dashboard/web_dashboard_node.py'

    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        sys.exit(1)

    if integrate_database(file_path):
        print("\n下一步：")
        print("1. 重新编译工作区: cd /mnt/sdcard/medicine_robot_ws && colcon build --packages-select medicine_web_dashboard")
        print("2. 重启 Web Dashboard 服务")
        print("3. 测试数据保存功能")
    else:
        print("\n无需操作")
