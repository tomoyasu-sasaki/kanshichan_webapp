"""
TTS System Management API Routes - システム管理API

TTSシステム管理機能のAPIエンドポイント群
サービス状態監視、サポート言語、クリーンアップ、設定管理を提供
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from services.tts.tts_service import TTSService
from services.voice_manager import VoiceManager
from utils.logger import setup_logger
from utils.exceptions import ValidationError, ServiceUnavailableError
from .tts_helpers import get_backend_path

logger = setup_logger(__name__)

# Blueprint定義
tts_system_bp = Blueprint('tts_system', __name__, url_prefix='/api/tts')

# サービスインスタンス（tts_helpers.pyで初期化）
tts_service: Optional[TTSService] = None
voice_manager: Optional[VoiceManager] = None


def init_system_services(tts_svc: TTSService, vm: VoiceManager) -> None:
    """システム管理サービスの初期化
    
    Args:
        tts_svc: TTSServiceインスタンス
        vm: VoiceManagerインスタンス
    """
    global tts_service, voice_manager
    tts_service = tts_svc
    voice_manager = vm


@tts_system_bp.route('/status', methods=['GET'])
def get_tts_status():
    """TTSサービス状態を取得
    
    Returns:
        JSON response with TTS service status
    """
    try:
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'services': {
                'tts_service': 'unavailable',
                'voice_manager': 'unavailable'
            },
            'system_health': 'unknown'
        }
        
        # TTS Service状態チェック
        tts_status_details = None
        if tts_service:
            try:
                tts_status_details = tts_service.get_service_status()
                response['services']['tts_service'] = 'available'
                response['tts_details'] = tts_status_details
            except Exception as e:
                logger.warning(f"Failed to get TTS service status: {e}")
                response['services']['tts_service'] = 'error'
                response['tts_error'] = str(e)
        
        # Voice Manager状態チェック
        if voice_manager:
            try:
                vm_status = voice_manager.get_service_status()
                response['services']['voice_manager'] = 'available'
                response['voice_manager_details'] = vm_status
            except Exception as e:
                logger.warning(f"Failed to get Voice Manager status: {e}")
                response['services']['voice_manager'] = 'error'
                response['voice_manager_error'] = str(e)
        
        # 全体的なシステムヘルス判定
        if (response['services']['tts_service'] == 'available' and 
            response['services']['voice_manager'] == 'available'):
            response['system_health'] = 'healthy'
        elif (response['services']['tts_service'] in ['available', 'error'] or 
              response['services']['voice_manager'] in ['available', 'error']):
            response['system_health'] = 'degraded'
        else:
            response['system_health'] = 'unavailable'
        
        # 機能別対応状況
        response['capabilities'] = {
            'text_synthesis': response['services']['tts_service'] == 'available',
            'voice_cloning': (response['services']['tts_service'] == 'available' and 
                            response['services']['voice_manager'] == 'available'),
            'file_management': response['services']['voice_manager'] == 'available',
            'emotion_processing': response['services']['tts_service'] == 'available'
        }
        
        # フロントエンドとの互換性のため、statusフィールドを追加
        response['status'] = {
            'tts_service': tts_status_details if tts_status_details else {
                'initialized': response['services']['tts_service'] == 'available',
                'model_name': 'Unknown',
                'device': 'Unknown',
                'voice_cloning_enabled': False,
                'default_language': 'ja',
                'supported_languages': ['ja'],
                'available_emotions': ['neutral']
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting TTS status: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to get TTS service status',
            'timestamp': datetime.now().isoformat()
        }), 500


@tts_system_bp.route('/languages', methods=['GET'])
def get_supported_languages():
    """サポートしている言語の一覧を取得
    
    Returns:
        JSON response with supported languages
    """
    if not tts_service:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'TTS service is not available'
        }), 503
    
    try:
        languages = tts_service.get_supported_languages()
        
        return jsonify({
            'success': True,
            'languages': languages,
            'total_count': len(languages),
            'default_language': 'ja'
        })
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to get supported languages'
        }), 500


@tts_system_bp.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    """古いファイルをクリーンアップ
    
    Request JSON:
        max_age_hours: 最大保持時間（時間単位、デフォルト: 24）
        file_types: クリーンアップ対象のファイルタイプリスト (optional)
                   Options: ["cache", "temp", "generated", "sample"]
        dry_run: 実際にはクリーンアップせず、対象ファイルのみ表示 (optional, default: false)
        force: 強制クリーンアップフラグ (optional, default: false)
    
    Returns:
        JSON response with cleanup result
    """
    if not voice_manager:
        return jsonify({
            'error': 'service_unavailable',
            'message': 'Voice manager is not available'
        }), 503
    
    try:
        # リクエストデータ取得
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', 24)
        file_types = data.get('file_types', ['cache', 'temp'])
        dry_run = data.get('dry_run', False)
        force = data.get('force', False)
        
        logger.info(f"🧹 Cleanup request: max_age={max_age_hours}h, types={file_types}, dry_run={dry_run}")
        
        # パラメータ検証
        if not isinstance(max_age_hours, (int, float)) or max_age_hours <= 0:
            raise ValidationError("max_age_hours must be a positive number")
        
        if not isinstance(file_types, list) or not all(isinstance(t, str) for t in file_types):
            raise ValidationError("file_types must be a list of strings")
        
        # Voice Managerを使ってクリーンアップ実行
        cleanup_result = voice_manager.cleanup_old_files(
            max_age_hours=max_age_hours,
            file_types=file_types,
            dry_run=dry_run,
            force=force
        )
        
        response = {
            'success': True,
            'cleanup_performed': not dry_run,
            'dry_run': dry_run,
            'max_age_hours': max_age_hours,
            'file_types': file_types,
            'results': cleanup_result
        }
        
        if dry_run:
            response['message'] = f"Dry run completed: {cleanup_result.get('total_files', 0)} files would be cleaned"
        else:
            response['message'] = f"Cleanup completed: {cleanup_result.get('deleted_files', 0)} files deleted"
        
        return jsonify(response)
        
    except ValidationError as e:
        logger.warning(f"Validation error in cleanup: {e}")
        return jsonify({
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to perform cleanup operation'
        }), 500


@tts_system_bp.route('/config', methods=['GET'])
def get_system_config():
    """システム設定情報を取得
    
    Returns:
        JSON response with system configuration
    """
    try:
        config = {
            'success': True,
            'configuration': {
                'backend_path': str(get_backend_path()),
                'services_available': {
                    'tts_service': tts_service is not None,
                    'voice_manager': voice_manager is not None
                }
            }
        }
        
        # TTS Service設定
        if tts_service:
            try:
                tts_config = tts_service.get_configuration()
                config['configuration']['tts_service'] = tts_config
            except Exception as e:
                logger.warning(f"Failed to get TTS configuration: {e}")
                config['configuration']['tts_service'] = {'error': str(e)}
        
        # Voice Manager設定
        if voice_manager:
            try:
                vm_config = voice_manager.get_configuration()
                config['configuration']['voice_manager'] = vm_config
            except Exception as e:
                logger.warning(f"Failed to get Voice Manager configuration: {e}")
                config['configuration']['voice_manager'] = {'error': str(e)}
        
        return jsonify(config)
        
    except Exception as e:
        logger.error(f"Error getting system configuration: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to get system configuration'
        }), 500


@tts_system_bp.route('/health', methods=['GET'])
def health_check():
    """システムヘルスチェック
    
    Returns:
        JSON response with detailed health status
    """
    try:
        health_status = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'components': {}
        }
        
        component_statuses = []
        
        # TTS Service ヘルスチェック
        if tts_service:
            try:
                tts_health = tts_service.health_check()
                health_status['components']['tts_service'] = tts_health
                component_statuses.append(tts_health.get('status', 'unknown'))
            except Exception as e:
                logger.warning(f"TTS service health check failed: {e}")
                health_status['components']['tts_service'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                component_statuses.append('unhealthy')
        else:
            health_status['components']['tts_service'] = {
                'status': 'unavailable',
                'message': 'Service not initialized'
            }
            component_statuses.append('unavailable')
        
        # Voice Manager ヘルスチェック
        if voice_manager:
            try:
                vm_health = voice_manager.health_check()
                health_status['components']['voice_manager'] = vm_health
                component_statuses.append(vm_health.get('status', 'unknown'))
            except Exception as e:
                logger.warning(f"Voice Manager health check failed: {e}")
                health_status['components']['voice_manager'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                component_statuses.append('unhealthy')
        else:
            health_status['components']['voice_manager'] = {
                'status': 'unavailable',
                'message': 'Service not initialized'
            }
            component_statuses.append('unavailable')
        
        # ディスク使用量チェック
        try:
            backend_path = get_backend_path()
            disk_usage = os.statvfs(backend_path)
            total_space = disk_usage.f_blocks * disk_usage.f_frsize
            free_space = disk_usage.f_bavail * disk_usage.f_frsize
            used_percentage = ((total_space - free_space) / total_space) * 100
            
            disk_status = 'healthy'
            if used_percentage > 90:
                disk_status = 'critical'
            elif used_percentage > 80:
                disk_status = 'warning'
            
            health_status['components']['disk_space'] = {
                'status': disk_status,
                'used_percentage': round(used_percentage, 2),
                'free_space_gb': round(free_space / (1024**3), 2),
                'total_space_gb': round(total_space / (1024**3), 2)
            }
            component_statuses.append(disk_status)
            
        except Exception as e:
            logger.warning(f"Disk space check failed: {e}")
            health_status['components']['disk_space'] = {
                'status': 'unknown',
                'error': str(e)
            }
            component_statuses.append('unknown')
        
        # 全体的なステータス判定
        if all(status == 'healthy' for status in component_statuses):
            health_status['overall_status'] = 'healthy'
        elif any(status == 'critical' for status in component_statuses):
            health_status['overall_status'] = 'critical'
        elif any(status in ['unhealthy', 'warning'] for status in component_statuses):
            health_status['overall_status'] = 'degraded'
        elif all(status == 'unavailable' for status in component_statuses):
            health_status['overall_status'] = 'unavailable'
        else:
            health_status['overall_status'] = 'unknown'
        
        # HTTPステータスコードの決定
        if health_status['overall_status'] in ['healthy', 'warning']:
            status_code = 200
        elif health_status['overall_status'] == 'degraded':
            status_code = 200  # 一部機能は利用可能
        else:
            status_code = 503  # サービス利用不可
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        return jsonify({
            'success': False,
            'overall_status': 'error',
            'error': 'internal_error',
            'message': 'Health check failed',
            'timestamp': datetime.now().isoformat()
        }), 500


@tts_system_bp.route('/metrics', methods=['GET'])
def get_system_metrics():
    """システムメトリクス取得
    
    Query Parameters:
        time_range: メトリクス期間 (optional, default: "1h")
                   Options: "1h", "6h", "24h", "7d"
        include_details: 詳細情報を含めるかどうか (optional, default: false)
    
    Returns:
        JSON response with system metrics
    """
    try:
        time_range = request.args.get('time_range', '1h')
        include_details = request.args.get('include_details', 'false').lower() == 'true'
        
        metrics = {
            'success': True,
            'time_range': time_range,
            'timestamp': datetime.now().isoformat(),
            'metrics': {}
        }
        
        # TTS Service メトリクス
        if tts_service:
            try:
                tts_metrics = tts_service.get_metrics(time_range=time_range)
                metrics['metrics']['tts_service'] = tts_metrics
            except Exception as e:
                logger.warning(f"Failed to get TTS metrics: {e}")
                metrics['metrics']['tts_service'] = {'error': str(e)}
        
        # Voice Manager メトリクス
        if voice_manager:
            try:
                vm_metrics = voice_manager.get_metrics(time_range=time_range)
                metrics['metrics']['voice_manager'] = vm_metrics
            except Exception as e:
                logger.warning(f"Failed to get Voice Manager metrics: {e}")
                metrics['metrics']['voice_manager'] = {'error': str(e)}
        
        # システムリソースメトリクス
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            system_metrics = {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2)
            }
            
            if include_details:
                disk_usage = psutil.disk_usage(str(get_backend_path()))
                system_metrics.update({
                    'disk_usage_percent': round((disk_usage.used / disk_usage.total) * 100, 2),
                    'disk_free_gb': round(disk_usage.free / (1024**3), 2),
                    'disk_total_gb': round(disk_usage.total / (1024**3), 2)
                })
            
            metrics['metrics']['system_resources'] = system_metrics
            
        except ImportError:
            logger.warning("psutil not available for system metrics")
            metrics['metrics']['system_resources'] = {
                'note': 'System resource monitoring not available'
            }
        except Exception as e:
            logger.warning(f"Failed to get system resource metrics: {e}")
            metrics['metrics']['system_resources'] = {'error': str(e)}
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to get system metrics'
        }), 500


@tts_system_bp.route('/restart', methods=['POST'])
def restart_services():
    """TTSサービスの再起動
    
    Request JSON:
        service: 再起動対象サービス (optional, default: "all")
                Options: "all", "tts", "voice_manager"
        force: 強制再起動フラグ (optional, default: false)
    
    Returns:
        JSON response with restart result
    """
    try:
        data = request.get_json() or {}
        service = data.get('service', 'all')
        force = data.get('force', False)
        
        logger.info(f"🔄 Service restart request: service={service}, force={force}")
        
        restart_results = {
            'success': True,
            'service': service,
            'force': force,
            'timestamp': datetime.now().isoformat(),
            'results': {}
        }
        
        # TTS Service再起動
        if service in ['all', 'tts'] and tts_service:
            try:
                tts_restart_result = tts_service.restart(force=force)
                restart_results['results']['tts_service'] = tts_restart_result
                logger.info("🔄 TTS Service restart completed")
            except Exception as e:
                logger.error(f"TTS Service restart failed: {e}")
                restart_results['results']['tts_service'] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Voice Manager再起動
        if service in ['all', 'voice_manager'] and voice_manager:
            try:
                vm_restart_result = voice_manager.restart(force=force)
                restart_results['results']['voice_manager'] = vm_restart_result
                logger.info("🔄 Voice Manager restart completed")
            except Exception as e:
                logger.error(f"Voice Manager restart failed: {e}")
                restart_results['results']['voice_manager'] = {
                    'success': False,
                    'error': str(e)
                }
        
        # 再起動結果の評価
        all_success = all(
            result.get('success', False) 
            for result in restart_results['results'].values()
        )
        
        if not all_success:
            restart_results['success'] = False
            restart_results['message'] = 'Some services failed to restart'
        else:
            restart_results['message'] = 'All services restarted successfully'
        
        status_code = 200 if all_success else 500
        return jsonify(restart_results), status_code
        
    except Exception as e:
        logger.error(f"Error during service restart: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to restart services',
            'timestamp': datetime.now().isoformat()
        }), 500 