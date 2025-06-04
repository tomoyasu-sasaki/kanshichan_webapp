#!/usr/bin/env python3
"""
Phase 5: E2Eテスト実行スクリプト
===============================
バックエンド統合テストの実行とレポート生成
"""
import os
import sys
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "backend" / "src"))

class Phase5TestRunner:
    """Phase 5 統合テストランナー"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.test_results: Dict[str, Any] = {
            'summary': {},
            'test_suites': {},
            'performance_metrics': {},
            'errors': []
        }
        
    def run_backend_tests(self) -> Dict[str, Any]:
        """バックエンド統合テストの実行"""
        print("🚀 Phase 5: バックエンド統合テスト開始")
        
        try:
            # Phase 5統合テストの実行
            cmd = [
                sys.executable, "-m", "pytest", 
                "backend/tests/test_integration_phase5.py",
                "-v", "--tb=short", "--json-report", "--json-report-file=test_report.json"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=project_root
            )
            
            # 結果の処理
            test_result = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            # JSONレポートの読み込み
            report_file = project_root / "test_report.json"
            if report_file.exists():
                with open(report_file, 'r') as f:
                    json_report = json.load(f)
                test_result['detailed_report'] = json_report
                
            self.test_results['test_suites']['backend_integration'] = test_result
            
            if test_result['success']:
                print("✅ バックエンド統合テスト: 成功")
            else:
                print("❌ バックエンド統合テスト: 失敗")
                print(f"エラー: {result.stderr}")
                
            return test_result
            
        except Exception as e:
            error_msg = f"バックエンドテスト実行エラー: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results['errors'].append(error_msg)
            return {'success': False, 'error': error_msg}
    
    def run_individual_phase_tests(self) -> Dict[str, Any]:
        """各Phase個別テストの実行"""
        print("🔍 個別Phaseテスト実行")
        
        phase_tests = {
            'phase1_monitor': 'backend/tests/test_monitor.py',
            'phase2_tts': 'backend/tests/test_flask_server.py',
            'phase3_integration': 'backend/tests/test_alert_system.py',
            'phase4_analysis': 'backend/tests/test_llm_service.py'
        }
        
        phase_results = {}
        
        for phase_name, test_file in phase_tests.items():
            try:
                print(f"  📋 {phase_name} テスト実行中...")
                
                cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"]
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    cwd=project_root
                )
                
                phase_results[phase_name] = {
                    'success': result.returncode == 0,
                    'exit_code': result.returncode,
                    'stdout': result.stdout[-500:] if len(result.stdout) > 500 else result.stdout,  # 最後の500文字
                    'stderr': result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
                }
                
                if result.returncode == 0:
                    print(f"  ✅ {phase_name}: 成功")
                else:
                    print(f"  ❌ {phase_name}: 失敗")
                    
            except Exception as e:
                error_msg = f"{phase_name}テスト実行エラー: {str(e)}"
                print(f"  ❌ {error_msg}")
                phase_results[phase_name] = {'success': False, 'error': error_msg}
                self.test_results['errors'].append(error_msg)
        
        self.test_results['test_suites']['individual_phases'] = phase_results
        return phase_results
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """パフォーマンステストの実行"""
        print("⚡ パフォーマンステスト実行")
        
        performance_metrics = {}
        
        try:
            # テスト実行時間測定
            start_time = time.time()
            
            # Phase 5統合テストを再実行してパフォーマンス測定
            cmd = [
                sys.executable, "-m", "pytest", 
                "backend/tests/test_integration_phase5.py::TestPhase5Integration::test_scalability_performance",
                "-v", "--tb=short"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=project_root
            )
            
            execution_time = time.time() - start_time
            
            performance_metrics = {
                'test_execution_time': execution_time,
                'scalability_test_passed': result.returncode == 0,
                'memory_usage': self._get_memory_usage(),
                'cpu_usage': self._get_cpu_usage()
            }
            
            self.test_results['performance_metrics'] = performance_metrics
            
            print(f"  📊 実行時間: {execution_time:.2f}秒")
            print(f"  📊 スケーラビリティテスト: {'✅ 成功' if result.returncode == 0 else '❌ 失敗'}")
            
            return performance_metrics
            
        except Exception as e:
            error_msg = f"パフォーマンステストエラー: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results['errors'].append(error_msg)
            return {'error': error_msg}
    
    def _get_memory_usage(self) -> float:
        """メモリ使用量取得（簡易版）"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """CPU使用量取得（簡易版）"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0
    
    def generate_report(self) -> Dict[str, Any]:
        """テスト結果レポートの生成"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # サマリーの計算
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        # バックエンド統合テスト
        backend_result = self.test_results['test_suites'].get('backend_integration', {})
        if backend_result.get('success'):
            passed_tests += 1
        else:
            failed_tests += 1
        total_tests += 1
        
        # 個別Phaseテスト
        phase_results = self.test_results['test_suites'].get('individual_phases', {})
        for phase_name, result in phase_results.items():
            total_tests += 1
            if result.get('success'):
                passed_tests += 1
            else:
                failed_tests += 1
        
        # サマリーの設定
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'overall_status': 'PASS' if failed_tests == 0 else 'FAIL'
        }
        
        return self.test_results
    
    def save_report(self, filename: str = None) -> str:
        """レポートをファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"phase5_test_report_{timestamp}.json"
        
        report_path = project_root / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 テストレポート保存: {report_path}")
        return str(report_path)
    
    def print_summary(self):
        """テスト結果サマリーの表示"""
        summary = self.test_results['summary']
        
        print("\n" + "="*60)
        print("🎯 Phase 5 テスト結果サマリー")
        print("="*60)
        print(f"総テスト数: {summary['total_tests']}")
        print(f"成功: {summary['passed']} ✅")
        print(f"失敗: {summary['failed']} ❌")
        print(f"成功率: {summary['success_rate']:.1f}%")
        print(f"実行時間: {summary['total_duration']:.2f}秒")
        print(f"総合結果: {summary['overall_status']}")
        
        if self.test_results['errors']:
            print("\n❌ エラー一覧:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        performance = self.test_results.get('performance_metrics', {})
        if performance:
            print(f"\n⚡ パフォーマンス:")
            print(f"  実行時間: {performance.get('test_execution_time', 0):.2f}秒")
            print(f"  メモリ使用量: {performance.get('memory_usage', 0):.1f}MB")
            print(f"  CPU使用率: {performance.get('cpu_usage', 0):.1f}%")
        
        print("="*60)

def main():
    """メイン実行関数"""
    print("🚀 Phase 5: 最終統合テスト実行開始")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    runner = Phase5TestRunner()
    
    try:
        # 1. バックエンド統合テストの実行
        runner.run_backend_tests()
        
        # 2. 個別Phaseテストの実行
        runner.run_individual_phase_tests()
        
        # 3. パフォーマンステストの実行
        runner.run_performance_tests()
        
        # 4. レポート生成
        runner.generate_report()
        
        # 5. レポート保存
        runner.save_report()
        
        # 6. サマリー表示
        runner.print_summary()
        
        # 7. 終了コードの設定
        summary = runner.test_results['summary']
        exit_code = 0 if summary['overall_status'] == 'PASS' else 1
        
        print(f"\n🏁 Phase 5 テスト完了 (終了コード: {exit_code})")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ テスト実行が中断されました")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n❌ 予期せぬエラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 