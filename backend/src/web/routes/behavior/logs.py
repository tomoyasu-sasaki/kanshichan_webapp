from flask import request
from typing import Dict, Any
from ...response_utils import success_response, error_response
from .blueprint import behavior_bp
from models.behavior_log import BehaviorLog


def _parse_bool(value: str):
    if value is None:
        return None
    if value.lower() in ['true', '1', 'yes']:
        return True
    if value.lower() in ['false', '0', 'no']:
        return False
    return None


def _validate_logs_params(args) -> Dict[str, Any]:
    params = {
        'page': int(args.get('page', 1)),
        'per_page': int(args.get('per_page', 20)),
        'start_date': args.get('start_date'),
        'end_date': args.get('end_date'),
        'user_id': args.get('user_id'),
        'focus_min': float(args.get('focus_min')) if args.get('focus_min') else None,
        'focus_max': float(args.get('focus_max')) if args.get('focus_max') else None,
        'smartphone_detected': _parse_bool(args.get('smartphone_detected')),
        'presence_status': args.get('presence_status'),
        'order_by': args.get('order_by', 'timestamp_desc'),
    }
    if params['page'] < 1:
        return {'error': 'Page must be >= 1', 'code': 'VALIDATION_ERROR'}
    if params['per_page'] < 1 or params['per_page'] > 100:
        return {'error': 'per_page must be between 1 and 100', 'code': 'VALIDATION_ERROR'}
    if params['focus_min'] is not None and (params['focus_min'] < 0 or params['focus_min'] > 1):
        return {'error': 'focus_min must be between 0.0 and 1.0', 'code': 'VALIDATION_ERROR'}
    if params['focus_max'] is not None and (params['focus_max'] < 0 or params['focus_max'] > 1):
        return {'error': 'focus_max must be between 0.0 and 1.0', 'code': 'VALIDATION_ERROR'}
    if params['presence_status'] and params['presence_status'] not in ['present', 'absent', 'unknown']:
        return {'error': 'Invalid presence_status', 'code': 'VALIDATION_ERROR'}
    if params['order_by'] not in ['timestamp_asc', 'timestamp_desc']:
        return {'error': 'Invalid order_by', 'code': 'VALIDATION_ERROR'}
    return params


def _build_log_filters(params: Dict[str, Any]) -> Dict[str, Any]:
    from datetime import datetime
    filters = {}
    if params['start_date']:
        try:
            filters['start_time'] = datetime.fromisoformat(params['start_date'].replace('Z', '+00:00'))
        except ValueError:
            pass
    if params['end_date']:
        try:
            filters['end_time'] = datetime.fromisoformat(params['end_date'].replace('Z', '+00:00'))
        except ValueError:
            pass
    filters['user_id'] = params['user_id']
    filters['focus_min'] = params['focus_min']
    filters['focus_max'] = params['focus_max']
    filters['smartphone_detected'] = params['smartphone_detected']
    filters['presence_status'] = params['presence_status']
    return filters


def _calculate_pagination(total_count: int, page: int, per_page: int) -> Dict[str, Any]:
    total_pages = (total_count + per_page - 1) // per_page
    return {
        'current_page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'total_count': total_count,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'next_page': page + 1 if page < total_pages else None,
        'prev_page': page - 1 if page > 1 else None,
    }


@behavior_bp.route('/logs', methods=['GET'])
def get_behavior_logs():
    try:
        params = _validate_logs_params(request.args)
        if 'error' in params:
            return error_response(params.get('error', 'Invalid parameters'), code=params.get('code', 'VALIDATION_ERROR'), status_code=400)
        filters = _build_log_filters(params)
        logs, total_count = BehaviorLog.get_logs_with_pagination(
            page=params['page'],
            per_page=params['per_page'],
            filters=filters,
            order_by=params['order_by'],
        )
        pagination_info = _calculate_pagination(total_count, params['page'], params['per_page'])
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'focus_level': log.focus_level,
                'smartphone_detected': log.smartphone_detected,
                'presence_status': log.presence_status,
                'detected_objects': log.detected_objects,
                'posture_data': log.posture_data,
                'screen_activity': log.screen_activity,
                'created_at': log.created_at.isoformat() if log.created_at else None,
            })
        return success_response({
            'logs': logs_data,
            'pagination': pagination_info,
            'filters_applied': {k: v for k, v in filters.items() if v is not None},
            'total_count': total_count,
        })
    except Exception as e:
        return error_response('Failed to retrieve behavior logs', code='DATA_RETRIEVAL_ERROR', status_code=500)


