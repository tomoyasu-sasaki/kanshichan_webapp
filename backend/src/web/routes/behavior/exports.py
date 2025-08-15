from flask import request, Response
from typing import Dict, Any, List
from datetime import datetime
from .blueprint import behavior_bp
from ...response_utils import success_response, error_response
from models.behavior_log import BehaviorLog


@behavior_bp.route('/export', methods=['GET'])
def export_behavior_data():
    try:
        export_format = request.args.get('format', 'csv')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        user_id = request.args.get('user_id')
        fields_str = request.args.get('fields', 'timestamp,focus_level,smartphone_detected,presence_status')
        if not start_date_str or not end_date_str:
            return error_response('start_date and end_date are required', code='VALIDATION_ERROR', status_code=400)
        if export_format not in ['csv', 'json']:
            return error_response('Invalid format. Must be csv or json', code='VALIDATION_ERROR', status_code=400)
        try:
            start_time = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError:
            return error_response('Invalid date format. Use ISO 8601 format', code='VALIDATION_ERROR', status_code=400)
        if (end_time - start_time).days > 90:
            return error_response('Export period cannot exceed 90 days', code='VALIDATION_ERROR', status_code=400)
        logs = BehaviorLog.get_logs_by_timerange(start_time=start_time, end_time=end_time, user_id=user_id)
        if not logs:
            return success_response({'message': 'No data found for the specified period', 'count': 0})
        available_fields = {
            'timestamp': lambda log: log.timestamp.isoformat(),
            'focus_level': lambda log: log.focus_level,
            'smartphone_detected': lambda log: log.smartphone_detected,
            'presence_status': lambda log: log.presence_status,
            'detected_objects': lambda log: log.detected_objects,
            'posture_data': lambda log: log.posture_data,
            'screen_activity': lambda log: log.screen_activity,
        }
        fields = [f.strip() for f in fields_str.split(',') if f.strip() in available_fields]
        if export_format == 'csv':
            csv_data = _generate_csv_export(logs, fields, available_fields)
            return csv_data
        else:
            json_data = _generate_json_export(logs, fields, available_fields)
            return success_response({
                'records': json_data,
                'count': len(json_data),
                'fields': fields,
                'export_info': {
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'generated_at': datetime.utcnow().isoformat(),
                },
            })
    except Exception:
        return error_response('Failed to export behavior data', code='EXPORT_ERROR', status_code=500)


def _generate_csv_export(logs: List, fields: List[str], field_map: Dict) -> Response:
    import io
    output = io.StringIO()
    output.write(','.join(fields) + '\n')
    for log in logs:
        row_data = []
        for field in fields:
            value = field_map[field](log)
            if isinstance(value, (dict, list)):
                value = str(value).replace(',', ';')
            row_data.append(str(value) if value is not None else '')
        output.write(','.join(row_data) + '\n')
    csv_content = output.getvalue()
    output.close()
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=behavior_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'},
    )


def _generate_json_export(logs: List, fields: List[str], field_map: Dict) -> List[Dict]:
    export_data = []
    for log in logs:
        record = {}
        for field in fields:
            record[field] = field_map[field](log)
        export_data.append(record)
    return export_data


