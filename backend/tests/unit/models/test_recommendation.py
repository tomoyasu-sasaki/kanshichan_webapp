"""
RecommendationSchema Unit Tests
"""

import pytest
import json
from datetime import datetime, timedelta

from backend.src.models.recommendation import RecommendationSchema, standardize_recommendations


def test_recommendation_schema_creation():
    """基本的なRecommendationSchemaインスタンス作成テスト"""
    rec = RecommendationSchema(
        type='focus_improvement',
        message='テストメッセージ',
        priority='high'
    )
    
    assert rec.type == 'focus_improvement'
    assert rec.message == 'テストメッセージ'
    assert rec.priority == 'high'
    
    # デフォルト値のチェック
    assert rec.action is None
    assert rec.emotion is None
    assert rec.audio_url is None
    assert rec.tts_requested is False
    assert isinstance(rec.metadata, dict)
    assert len(rec.metadata) == 0
    
    # タイムスタンプが生成されていることを確認
    assert rec.timestamp is not None


def test_recommendation_schema_to_dict():
    """to_dict()メソッドのテスト"""
    rec = RecommendationSchema(
        type='distraction_management',
        message='スマホは手元から離しましょう',
        priority='medium',
        action='phone_away',
        emotion='encouraging',
        source='test_source'
    )
    
    dict_data = rec.to_dict()
    
    assert dict_data['type'] == 'distraction_management'
    assert dict_data['message'] == 'スマホは手元から離しましょう'
    assert dict_data['priority'] == 'medium'
    assert dict_data['action'] == 'phone_away'
    assert dict_data['emotion'] == 'encouraging'
    assert dict_data['source'] == 'test_source'
    assert 'timestamp' in dict_data
    
    # None値のフィールドはdictに含まれないことを確認
    assert 'audio_url' not in dict_data
    assert 'voice_text' not in dict_data


def test_recommendation_schema_to_json():
    """to_json()メソッドのテスト"""
    rec = RecommendationSchema(
        type='test_type',
        message='テストJSON変換',
        priority='low',
        action='test_action'
    )
    
    json_str = rec.to_json()
    parsed = json.loads(json_str)
    
    assert parsed['type'] == 'test_type'
    assert parsed['message'] == 'テストJSON変換'
    assert parsed['priority'] == 'low'
    assert parsed['action'] == 'test_action'


def test_recommendation_schema_from_dict():
    """from_dict()メソッドのテスト"""
    test_dict = {
        'type': 'focus_training',
        'message': '集中力を高めるためのトレーニング',
        'priority': 'high',
        'action': 'pomodoro',
        'emotion': 'motivational',
        'tts_requested': True,
        'audio_url': '/test/url.mp3',
        'invalid_field': 'should be ignored'
    }
    
    rec = RecommendationSchema.from_dict(test_dict)
    
    assert rec.type == 'focus_training'
    assert rec.message == '集中力を高めるためのトレーニング'
    assert rec.priority == 'high'
    assert rec.action == 'pomodoro'
    assert rec.emotion == 'motivational'
    assert rec.tts_requested is True
    assert rec.audio_url == '/test/url.mp3'
    
    # 無効なフィールドは無視されるべき
    assert not hasattr(rec, 'invalid_field')


def test_from_analyzer_format():
    """from_analyzer_format()メソッドのテスト"""
    analyzer_format = {
        'type': 'break_recommendation',
        'message': '休憩を取りましょう',
        'priority': 'medium',
        'action': 'take_break'
    }
    
    rec = RecommendationSchema.from_analyzer_format(analyzer_format)
    
    assert rec.type == 'break_recommendation'
    assert rec.message == '休憩を取りましょう'
    assert rec.priority == 'medium'
    assert rec.action == 'take_break'
    assert rec.source == 'behavior_analysis'
    assert rec.timestamp is not None


def test_from_advice_generator_format():
    """from_advice_generator_format()メソッドのテスト"""
    advice_format = {
        'advice_text': 'アドバイステキスト',
        'priority': 'high',
        'emotion': 'encouraging',
        'generation_timestamp': '2025-06-12T12:00:00Z'
    }
    
    rec = RecommendationSchema.from_advice_generator_format(advice_format)
    
    assert rec.type == 'contextual_advice'
    assert rec.message == 'アドバイステキスト'
    assert rec.priority == 'high'
    assert rec.emotion == 'encouraging'
    assert rec.source == 'llm_advice'
    assert rec.timestamp == '2025-06-12T12:00:00Z'


def test_standardize_recommendations():
    """standardize_recommendations()関数のテスト"""
    # 混合フォーマットの推奨事項リスト
    mixed_recommendations = [
        # すでにRecommendationSchema
        RecommendationSchema(
            type='already_schema',
            message='すでにスキーマ',
            priority='high'
        ),
        # analyzer形式
        {
            'type': 'analyzer_format',
            'message': 'アナライザー形式',
            'priority': 'medium',
            'action': 'some_action',
            'source': 'behavior_analysis'
        },
        # advice_generator形式
        {
            'advice_text': 'アドバイス形式',
            'priority': 'low',
            'emotion': 'gentle',
            'source': 'llm_advice'
        }
    ]
    
    standardized = standardize_recommendations(mixed_recommendations)
    
    # 全て変換されていることを確認
    assert len(standardized) == 3
    
    # 全てRecommendationSchemaになっていることを確認
    for rec in standardized:
        assert isinstance(rec, RecommendationSchema)
    
    # 元の情報が保持されていることを確認
    assert standardized[0].type == 'already_schema'
    assert standardized[1].type == 'analyzer_format'
    assert standardized[2].type == 'contextual_advice'
    assert standardized[2].message == 'アドバイス形式'


def test_recommendation_schema_audio_fields():
    """音声関連フィールドのテスト"""
    rec = RecommendationSchema(
        type='audio_test',
        message='音声テスト',
        priority='medium',
        audio_url='/api/tts/test.mp3',
        voice_text='これは音声合成用のテキストです',
        tts_requested=True
    )
    
    assert rec.audio_url == '/api/tts/test.mp3'
    assert rec.voice_text == 'これは音声合成用のテキストです'
    assert rec.tts_requested is True
    
    # 辞書変換でも保持されることを確認
    dict_data = rec.to_dict()
    assert dict_data['audio_url'] == '/api/tts/test.mp3'
    assert dict_data['voice_text'] == 'これは音声合成用のテキストです'
    assert dict_data['tts_requested'] is True 