#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配送数据持久化模块
使用 SQLite 数据库保存配送批次、扫码记录和审计日志
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os


class DeliveryDatabase:
    """配送数据库管理类"""

    def __init__(self, db_path: str = "/mnt/sdcard/medicine_robot_data/delivery.db"):
        """初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # 返回字典格式
        self._create_tables()

    def _create_tables(self):
        """创建数据库表结构"""
        cursor = self.conn.cursor()

        # 配送批次表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_batches (
                batch_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT NOT NULL,
                source_station TEXT,
                route_json TEXT,
                operator_id TEXT,
                total_stops INTEGER DEFAULT 0,
                total_patients INTEGER DEFAULT 0,
                total_medications INTEGER DEFAULT 0,
                completed_medications INTEGER DEFAULT 0,
                failed_medications INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')

        # 扫码记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                stage TEXT NOT NULL,
                product_code TEXT,
                trace_id TEXT,
                patient_id TEXT,
                patient_name TEXT,
                medication_name TEXT,
                result TEXT NOT NULL,
                expected_product_code TEXT,
                expected_trace_id TEXT,
                operator TEXT,
                station TEXT,
                notes TEXT,
                FOREIGN KEY (batch_id) REFERENCES delivery_batches(batch_id)
            )
        ''')

        # 异常记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exception_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exception_type TEXT NOT NULL,
                patient_id TEXT,
                medication_id TEXT,
                station TEXT,
                description TEXT,
                resolved BOOLEAN DEFAULT 0,
                resolved_at TIMESTAMP,
                resolution_action TEXT,
                resolution_reason TEXT,
                FOREIGN KEY (batch_id) REFERENCES delivery_batches(batch_id)
            )
        ''')

        # 系统日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                category TEXT,
                message TEXT NOT NULL,
                details TEXT
            )
        ''')

        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scan_batch
            ON scan_records(batch_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scan_timestamp
            ON scan_records(timestamp)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_exception_batch
            ON exception_records(batch_id)
        ''')

        self.conn.commit()

    def save_batch(self, batch_data: Dict[str, Any]) -> bool:
        """保存配送批次

        Args:
            batch_data: 批次数据字典

        Returns:
            是否保存成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO delivery_batches
                (batch_id, status, source_station, route_json, operator_id,
                 total_stops, total_patients, total_medications,
                 completed_medications, failed_medications, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                batch_data.get('batch_id'),
                batch_data.get('status'),
                batch_data.get('source_station'),
                json.dumps(batch_data.get('route', []), ensure_ascii=False),
                batch_data.get('operator_id'),
                batch_data.get('total_stops', 0),
                batch_data.get('total_patients', 0),
                batch_data.get('total_medications', 0),
                batch_data.get('completed_medications', 0),
                batch_data.get('failed_medications', 0),
                batch_data.get('notes')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存批次失败: {e}")
            return False

    def save_scan_record(self, batch_id: str, stage: str,
                        product_code: str, trace_id: str,
                        result: str, **kwargs) -> bool:
        """保存扫码记录

        Args:
            batch_id: 批次ID
            stage: 阶段 (load/dispense)
            product_code: 产品编码
            trace_id: 追溯编号
            result: 结果 (success/mismatch/error)
            **kwargs: 其他可选参数

        Returns:
            是否保存成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO scan_records
                (batch_id, stage, product_code, trace_id, result,
                 patient_id, patient_name, medication_name,
                 expected_product_code, expected_trace_id,
                 operator, station, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                batch_id,
                stage,
                product_code,
                trace_id,
                result,
                kwargs.get('patient_id'),
                kwargs.get('patient_name'),
                kwargs.get('medication_name'),
                kwargs.get('expected_product_code'),
                kwargs.get('expected_trace_id'),
                kwargs.get('operator'),
                kwargs.get('station'),
                kwargs.get('notes')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存扫码记录失败: {e}")
            return False

    def save_exception(self, batch_id: str, exception_type: str,
                      description: str, **kwargs) -> bool:
        """保存异常记录

        Args:
            batch_id: 批次ID
            exception_type: 异常类型
            description: 异常描述
            **kwargs: 其他可选参数

        Returns:
            是否保存成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO exception_records
                (batch_id, exception_type, patient_id, medication_id,
                 station, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                batch_id,
                exception_type,
                kwargs.get('patient_id'),
                kwargs.get('medication_id'),
                kwargs.get('station'),
                description
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存异常记录失败: {e}")
            return False

    def get_batch_scan_records(self, batch_id: str) -> List[Dict]:
        """获取批次的所有扫码记录

        Args:
            batch_id: 批次ID

        Returns:
            扫码记录列表
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM scan_records
            WHERE batch_id = ?
            ORDER BY timestamp DESC
        ''', (batch_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_batch_exceptions(self, batch_id: str) -> List[Dict]:
        """获取批次的所有异常记录

        Args:
            batch_id: 批次ID

        Returns:
            异常记录列表
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM exception_records
            WHERE batch_id = ?
            ORDER BY timestamp DESC
        ''', (batch_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_recent_batches(self, limit: int = 10) -> List[Dict]:
        """获取最近的配送批次

        Args:
            limit: 返回数量限制

        Returns:
            批次列表
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM delivery_batches
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def log_system_event(self, level: str, category: str,
                        message: str, details: Optional[str] = None):
        """记录系统日志

        Args:
            level: 日志级别 (INFO/WARNING/ERROR)
            category: 分类
            message: 消息
            details: 详细信息
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO system_logs (level, category, message, details)
                VALUES (?, ?, ?, ?)
            ''', (level, category, message, details))
            self.conn.commit()
        except Exception as e:
            print(f"记录系统日志失败: {e}")

    def export_batch_report(self, batch_id: str) -> Dict[str, Any]:
        """导出批次完整报告

        Args:
            batch_id: 批次ID

        Returns:
            包含批次信息、扫码记录、异常记录的完整报告
        """
        cursor = self.conn.cursor()

        # 获取批次信息
        cursor.execute('SELECT * FROM delivery_batches WHERE batch_id = ?', (batch_id,))
        batch = cursor.fetchone()

        if not batch:
            return {}

        # 获取扫码记录
        scan_records = self.get_batch_scan_records(batch_id)

        # 获取异常记录
        exceptions = self.get_batch_exceptions(batch_id)

        return {
            'batch': dict(batch),
            'scan_records': scan_records,
            'exceptions': exceptions,
            'export_time': datetime.now().isoformat()
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息

        Returns:
            统计信息字典
        """
        cursor = self.conn.cursor()

        # 总批次数
        cursor.execute('SELECT COUNT(*) FROM delivery_batches')
        total_batches = cursor.fetchone()[0]

        # 总扫码记录数
        cursor.execute('SELECT COUNT(*) FROM scan_records')
        total_scans = cursor.fetchone()[0]

        # 总异常记录数
        cursor.execute('SELECT COUNT(*) FROM exception_records')
        total_exceptions = cursor.fetchone()[0]

        # 成功扫码数
        cursor.execute("SELECT COUNT(*) FROM scan_records WHERE result = 'success'")
        successful_scans = cursor.fetchone()[0]

        # 未解决异常数
        cursor.execute('SELECT COUNT(*) FROM exception_records WHERE resolved = 0')
        unresolved_exceptions = cursor.fetchone()[0]

        return {
            'total_batches': total_batches,
            'total_scans': total_scans,
            'total_exceptions': total_exceptions,
            'successful_scans': successful_scans,
            'failed_scans': total_scans - successful_scans,
            'unresolved_exceptions': unresolved_exceptions,
            'success_rate': f"{successful_scans / total_scans * 100:.1f}%" if total_scans > 0 else "N/A"
        }

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


# 测试代码
if __name__ == '__main__':
    print("=== 配送数据库模块测试 ===")

    # 创建数据库实例
    db = DeliveryDatabase('/tmp/test_delivery.db')

    # 测试保存批次
    batch_data = {
        'batch_id': 'BATCH-20260531-001',
        'status': 'PREPARING',
        'source_station': 'pharmacy',
        'operator_id': 'operator_001',
        'total_stops': 3,
        'total_patients': 5,
        'total_medications': 10
    }

    if db.save_batch(batch_data):
        print("✓ 批次保存成功")

    # 测试保存扫码记录
    if db.save_scan_record(
        batch_id='BATCH-20260531-001',
        stage='load',
        product_code='C177248',
        trace_id='202011444',
        result='success',
        patient_id='patient_001',
        patient_name='张三',
        medication_name='降压药'
    ):
        print("✓ 扫码记录保存成功")

    # 测试保存异常
    if db.save_exception(
        batch_id='BATCH-20260531-001',
        exception_type='patient_absent',
        description='患者暂时不在病房',
        patient_id='patient_002',
        station='ward_a'
    ):
        print("✓ 异常记录保存成功")

    # 测试查询
    records = db.get_batch_scan_records('BATCH-20260531-001')
    print(f"✓ 查询到 {len(records)} 条扫码记录")

    # 测试导出报告
    report = db.export_batch_report('BATCH-20260531-001')
    print(f"✓ 导出报告成功，包含 {len(report.get('scan_records', []))} 条扫码记录")

    # 测试系统日志
    db.log_system_event('INFO', 'test', '测试日志记录')
    print("✓ 系统日志记录成功")

    # 测试统计信息
    stats = db.get_statistics()
    print(f"✓ 统计信息: {stats}")

    db.close()
    print("\n所有测试通过！")
