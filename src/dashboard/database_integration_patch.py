#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Dashboard 数据库集成补丁
用于在现有的 medicine_web_dashboard 中集成数据持久化功能

使用方法:
1. 将此文件放在 medicine_web_dashboard 目录
2. 在 web_dashboard_node.py 中导入并使用
"""

from delivery_database import DeliveryDatabase
import json
from datetime import datetime


class DatabaseIntegrationMixin:
    """数据库集成混入类

    将此类混入到现有的 WebDashboardNode 中
    """

    def init_database(self):
        """初始化数据库"""
        try:
            self.db = DeliveryDatabase()
            self.get_logger().info('✓ 数据库初始化成功')
            return True
        except Exception as e:
            self.get_logger().error(f'✗ 数据库初始化失败: {e}')
            self.db = None
            return False

    def save_batch_to_db(self, batch_data):
        """保存批次到数据库

        Args:
            batch_data: 批次数据字典

        Returns:
            是否保存成功
        """
        if not self.db:
            return False

        try:
            success = self.db.save_batch(batch_data)
            if success:
                self.get_logger().info(f'✓ 批次已保存到数据库: {batch_data.get("batch_id")}')
            return success
        except Exception as e:
            self.get_logger().error(f'✗ 保存批次失败: {e}')
            return False

    def save_scan_to_db(self, batch_id, stage, scan_data, result):
        """保存扫码记录到数据库

        Args:
            batch_id: 批次ID
            stage: 阶段 (load/dispense)
            scan_data: 扫码数据
            result: 验证结果 (True/False)

        Returns:
            是否保存成功
        """
        if not self.db:
            return False

        try:
            success = self.db.save_scan_record(
                batch_id=batch_id,
                stage=stage,
                product_code=scan_data.get('product_code', ''),
                trace_id=scan_data.get('trace_id', ''),
                result='success' if result else 'mismatch',
                patient_id=scan_data.get('patient_id'),
                patient_name=scan_data.get('patient_name'),
                medication_name=scan_data.get('medication_name'),
                expected_product_code=scan_data.get('expected_product_code'),
                expected_trace_id=scan_data.get('expected_trace_id'),
                operator=scan_data.get('operator', 'system'),
                station=scan_data.get('station')
            )

            if success:
                self.get_logger().info(
                    f'✓ 扫码记录已保存: {stage} {scan_data.get("product_code")} -> '
                    f'{"success" if result else "mismatch"}'
                )
            return success
        except Exception as e:
            self.get_logger().error(f'✗ 保存扫码记录失败: {e}')
            return False

    def save_exception_to_db(self, batch_id, exception_type, description, **kwargs):
        """保存异常记录到数据库

        Args:
            batch_id: 批次ID
            exception_type: 异常类型
            description: 异常描述
            **kwargs: 其他参数

        Returns:
            是否保存成功
        """
        if not self.db:
            return False

        try:
            success = self.db.save_exception(
                batch_id=batch_id,
                exception_type=exception_type,
                description=description,
                **kwargs
            )

            if success:
                self.get_logger().info(f'✓ 异常记录已保存: {exception_type}')
            return success
        except Exception as e:
            self.get_logger().error(f'✗ 保存异常记录失败: {e}')
            return False

    def get_batch_history_from_db(self, batch_id):
        """从数据库获取批次历史

        Args:
            batch_id: 批次ID

        Returns:
            包含扫码记录和异常记录的字典
        """
        if not self.db:
            return {'scan_records': [], 'exceptions': []}

        try:
            scan_records = self.db.get_batch_scan_records(batch_id)
            exceptions = self.db.get_batch_exceptions(batch_id)

            return {
                'scan_records': scan_records,
                'exceptions': exceptions
            }
        except Exception as e:
            self.get_logger().error(f'✗ 查询批次历史失败: {e}')
            return {'scan_records': [], 'exceptions': []}

    def export_batch_report_from_db(self, batch_id):
        """从数据库导出批次报告

        Args:
            batch_id: 批次ID

        Returns:
            完整报告字典
        """
        if not self.db:
            return {}

        try:
            report = self.db.export_batch_report(batch_id)
            return report
        except Exception as e:
            self.get_logger().error(f'✗ 导出报告失败: {e}')
            return {}

    def get_statistics_from_db(self):
        """从数据库获取统计信息

        Returns:
            统计信息字典
        """
        if not self.db:
            return {}

        try:
            stats = self.db.get_statistics()
            return stats
        except Exception as e:
            self.get_logger().error(f'✗ 获取统计信息失败: {e}')
            return {}


# 使用示例
"""
在 web_dashboard_node.py 中:

from database_integration_patch import DatabaseIntegrationMixin

class WebDashboardNode(Node, DatabaseIntegrationMixin):
    def __init__(self):
        super().__init__('medicine_web_dashboard')

        # 初始化数据库
        self.init_database()

        # ... 其他初始化代码

# 在 API 端点中使用:

@app.route('/api/delivery_batch', methods=['POST'])
def create_batch():
    batch_data = request.json

    # 保存到数据库
    self.save_batch_to_db(batch_data)

    # ... 其他逻辑
    return jsonify({'success': True})

@app.route('/api/delivery_batch/load_scan', methods=['POST'])
def load_scan():
    data = request.json

    # 验证逻辑
    result = verify_scan(data)

    # 保存扫码记录
    self.save_scan_to_db(
        batch_id=data['batch_id'],
        stage='load',
        scan_data=data,
        result=result
    )

    return jsonify({'verified': result})

@app.route('/api/batch/<batch_id>/history', methods=['GET'])
def get_history(batch_id):
    history = self.get_batch_history_from_db(batch_id)
    return jsonify(history)

@app.route('/api/statistics', methods=['GET'])
def get_stats():
    stats = self.get_statistics_from_db()
    return jsonify(stats)
"""
