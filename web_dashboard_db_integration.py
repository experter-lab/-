#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Dashboard 数据库集成示例
展示如何在现有的 medicine_web_dashboard 中集成数据持久化
"""

import sys
sys.path.insert(0, '/tmp')

from delivery_database import DeliveryDatabase
from datetime import datetime
import json


class WebDashboardWithDB:
    """带数据库的 Web Dashboard 示例"""

    def __init__(self):
        self.db = DeliveryDatabase()
        print("✓ 数据库初始化成功")

    def handle_create_batch(self, batch_data):
        """处理创建配送批次请求"""
        print("\n=== 创建配送批次 ===")

        # 保存到数据库
        success = self.db.save_batch(batch_data)

        if success:
            print(f"✓ 批次 {batch_data['batch_id']} 已保存到数据库")

            # 记录系统日志
            self.db.log_system_event(
                'INFO',
                'batch_management',
                f"创建配送批次: {batch_data['batch_id']}",
                json.dumps(batch_data, ensure_ascii=False)
            )

        return success

    def handle_scan_verification(self, batch_id, stage, scan_data):
        """处理扫码验证请求"""
        print(f"\n=== 扫码验证 ({stage}) ===")

        product_code = scan_data.get('product_code')
        trace_id = scan_data.get('trace_id')
        expected_code = scan_data.get('expected_product_code')
        expected_trace = scan_data.get('expected_trace_id')

        # 验证逻辑
        if product_code == expected_code and trace_id == expected_trace:
            result = 'success'
            print(f"✓ 扫码验证通过: {product_code} / {trace_id}")
        else:
            result = 'mismatch'
            print(f"✗ 扫码不匹配:")
            print(f"  期望: {expected_code} / {expected_trace}")
            print(f"  实际: {product_code} / {trace_id}")

        # 保存扫码记录到数据库
        self.db.save_scan_record(
            batch_id=batch_id,
            stage=stage,
            product_code=product_code,
            trace_id=trace_id,
            result=result,
            patient_id=scan_data.get('patient_id'),
            patient_name=scan_data.get('patient_name'),
            medication_name=scan_data.get('medication_name'),
            expected_product_code=expected_code,
            expected_trace_id=expected_trace,
            operator=scan_data.get('operator', 'system'),
            station=scan_data.get('station')
        )

        return result == 'success'

    def handle_exception(self, batch_id, exception_data):
        """处理异常情况"""
        print(f"\n=== 记录异常 ===")

        exception_type = exception_data.get('type')
        description = exception_data.get('description')

        print(f"异常类型: {exception_type}")
        print(f"描述: {description}")

        # 保存异常记录
        self.db.save_exception(
            batch_id=batch_id,
            exception_type=exception_type,
            description=description,
            patient_id=exception_data.get('patient_id'),
            medication_id=exception_data.get('medication_id'),
            station=exception_data.get('station')
        )

        # 记录系统日志
        self.db.log_system_event(
            'WARNING',
            'exception',
            f"配送异常: {exception_type}",
            description
        )

    def get_batch_history(self, batch_id):
        """获取批次完整历史"""
        print(f"\n=== 查询批次历史: {batch_id} ===")

        # 获取扫码记录
        scan_records = self.db.get_batch_scan_records(batch_id)
        print(f"扫码记录: {len(scan_records)} 条")

        for record in scan_records[:3]:  # 显示前3条
            print(f"  - {record['timestamp']}: {record['stage']} "
                  f"{record['product_code']} -> {record['result']}")

        # 获取异常记录
        exceptions = self.db.get_batch_exceptions(batch_id)
        print(f"异常记录: {len(exceptions)} 条")

        for exc in exceptions[:3]:  # 显示前3条
            print(f"  - {exc['timestamp']}: {exc['exception_type']} "
                  f"- {exc['description']}")

        return {
            'scan_records': scan_records,
            'exceptions': exceptions
        }

    def export_report(self, batch_id):
        """导出配送报告"""
        print(f"\n=== 导出配送报告: {batch_id} ===")

        report = self.db.export_batch_report(batch_id)

        if report:
            print(f"✓ 报告导出成功")
            print(f"  批次状态: {report['batch']['status']}")
            print(f"  扫码记录: {len(report['scan_records'])} 条")
            print(f"  异常记录: {len(report['exceptions'])} 条")
            print(f"  导出时间: {report['export_time']}")

            # 保存为 JSON 文件
            filename = f"/tmp/batch_report_{batch_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"  已保存到: {filename}")

        return report

    def get_dashboard_statistics(self):
        """获取 Dashboard 统计信息"""
        print("\n=== Dashboard 统计信息 ===")

        stats = self.db.get_statistics()

        print(f"总批次数: {stats['total_batches']}")
        print(f"总扫码数: {stats['total_scans']}")
        print(f"成功扫码: {stats['successful_scans']}")
        print(f"失败扫码: {stats['failed_scans']}")
        print(f"成功率: {stats['success_rate']}")
        print(f"总异常数: {stats['total_exceptions']}")
        print(f"未解决异常: {stats['unresolved_exceptions']}")

        return stats


# 演示完整流程
def demo_complete_workflow():
    """演示完整的配送流程"""
    print("=" * 60)
    print("配送数据持久化完整流程演示")
    print("=" * 60)

    dashboard = WebDashboardWithDB()

    # 1. 创建配送批次
    batch_data = {
        'batch_id': 'BATCH-20260531-DEMO',
        'status': 'PREPARING',
        'source_station': 'pharmacy',
        'operator_id': 'nurse_001',
        'total_stops': 2,
        'total_patients': 3,
        'total_medications': 5
    }
    dashboard.handle_create_batch(batch_data)

    # 2. 装药扫码验证（成功）
    scan_data_1 = {
        'product_code': 'C177248',
        'trace_id': '202011444',
        'expected_product_code': 'C177248',
        'expected_trace_id': '202011444',
        'patient_id': 'patient_001',
        'patient_name': '张三',
        'medication_name': '降压药',
        'station': 'pharmacy'
    }
    dashboard.handle_scan_verification('BATCH-20260531-DEMO', 'load', scan_data_1)

    # 3. 装药扫码验证（失败）
    scan_data_2 = {
        'product_code': 'C177248',
        'trace_id': '202011445',  # 错误的追溯号
        'expected_product_code': 'C177248',
        'expected_trace_id': '202011444',
        'patient_id': 'patient_002',
        'patient_name': '李四',
        'medication_name': '消炎药',
        'station': 'pharmacy'
    }
    dashboard.handle_scan_verification('BATCH-20260531-DEMO', 'load', scan_data_2)

    # 4. 记录异常
    exception_data = {
        'type': 'patient_absent',
        'description': '患者暂时不在病房，稍后重试',
        'patient_id': 'patient_003',
        'station': 'ward_a'
    }
    dashboard.handle_exception('BATCH-20260531-DEMO', exception_data)

    # 5. 到站取药扫码
    scan_data_3 = {
        'product_code': 'C177248',
        'trace_id': '202011444',
        'expected_product_code': 'C177248',
        'expected_trace_id': '202011444',
        'patient_id': 'patient_001',
        'patient_name': '张三',
        'medication_name': '降压药',
        'station': 'ward_a'
    }
    dashboard.handle_scan_verification('BATCH-20260531-DEMO', 'dispense', scan_data_3)

    # 6. 查询批次历史
    dashboard.get_batch_history('BATCH-20260531-DEMO')

    # 7. 导出报告
    dashboard.export_report('BATCH-20260531-DEMO')

    # 8. 显示统计信息
    dashboard.get_dashboard_statistics()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == '__main__':
    demo_complete_workflow()
