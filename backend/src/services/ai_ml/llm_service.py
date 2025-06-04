"""
LLM Service

ローカルLLM（Ollama）を使用した行動分析とアドバイス生成
Phase 3.2: パフォーマンス最適化実装
"""

from typing import Dict, Any, List, Optional
import json
import logging
import ollama
import hashlib
import time
from datetime import datetime, timedelta
from functools import lru_cache
import threading

from utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMService:
    """ローカルLLMサービス (パフォーマンス最適化版)
    
    Ollamaを使用してローカルでLLM推論を実行
    - ELYZA Llama-3-JP (日本語特化)
    - Qwen2:7b (多言語対応)
    - Phase 3.2: キャッシュ、バッチ処理、最適化
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config.get('llm', {})
        self.primary_model = self.config.get('primary_model', 'huggingface.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:latest')
        self.fallback_model = self.config.get('fallback_model', 'qwen2:7b')
        self.temperature = self.config.get('temperature', 0.7)
        self.max_tokens = self.config.get('max_tokens', 300)
        
        # フォールバックモードフラグ（初期化）
        self.fallback_mode = False
        
        # Phase 3.2: パフォーマンス最適化設定
        self.cache_enabled = self.config.get('enable_cache', True)
        self.cache_ttl = self.config.get('cache_ttl_hours', 24)
        self.batch_size = self.config.get('batch_size', 5)
        self.inference_timeout = self.config.get('inference_timeout_seconds', 30)
        
        # キャッシュとバッチ処理用のストレージ
        self._response_cache = {}
        self._batch_queue = []
        self._cache_lock = threading.Lock()
        self._batch_lock = threading.Lock()
        
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """モデルの初期化とヘルスチェック"""
        try:
            # Ollamaクライアントの初期化
            self.client = ollama.Client()
            
            # 利用可能モデルの確認（エラーハンドリング強化）
            available_models = []
            try:
                models_response = self.client.list()
                logger.debug(f"Ollama models response: {models_response}")
                
                if hasattr(models_response, 'models') and models_response.models:
                    for model in models_response.models:
                        # Pydanticモデルの場合
                        if hasattr(model, 'model'):
                            available_models.append(model.model)
                        # 辞書の場合（後方互換性）
                        elif isinstance(model, dict) and 'name' in model:
                            available_models.append(model['name'])
                        else:
                            logger.warning(f"Unexpected model format: {model}")
                else:
                    logger.warning(f"No models found in response: {models_response}")
                    
            except Exception as model_list_error:
                logger.warning(f"Failed to get model list from Ollama: {model_list_error}")
                # Ollamaサーバーが起動していない可能性があるため、フォールバックモードに移行
                available_models = []
            
            # モデル選択ロジック（フォールバック機能強化）
            if available_models:
                # プライマリモデルの確認
                if self.primary_model in available_models:
                    self.active_model = self.primary_model
                    logger.info(f"Primary model available: {self.primary_model}")
                elif self.fallback_model in available_models:
                    self.active_model = self.fallback_model
                    logger.warning(f"Primary model not found, using fallback: {self.fallback_model}")
                else:
                    # 利用可能なモデルがあるが、設定されたモデルがない場合
                    self.active_model = available_models[0]
                    logger.warning(f"Configured models not found, using first available: {self.active_model}")
            else:
                # モデルが全く利用できない場合のフォールバック
                logger.warning("No Ollama models available, LLM features will use fallback responses")
                self.active_model = None
                # LLMサービスを無効モードで初期化（フォールバック応答のみ）
                self._enable_fallback_mode()
                return
            
            # Phase 3.2: モデル最適化設定（モデルが利用可能な場合のみ）
            try:
                self._optimize_model_settings()
            except Exception as optimize_error:
                logger.warning(f"Model optimization failed, using defaults: {optimize_error}")
            
            logger.info(f"LLM Service initialized with optimizations, model: {self.active_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Service: {e}")
            # 完全フォールバックモード
            logger.warning("Initializing LLM Service in fallback mode")
            self.active_model = None
            self._enable_fallback_mode()
    
    def _enable_fallback_mode(self) -> None:
        """フォールバックモードを有効化
        
        Ollamaが利用できない場合でもシステムが動作するように
        事前定義された応答を使用するモードに切り替える
        """
        self.fallback_mode = True
        self.active_model = "fallback_mode"
        logger.info("LLM Service initialized in fallback mode - will use predefined responses")
    
    def _optimize_model_settings(self) -> None:
        """モデル推論設定の最適化"""
        try:
            # モデル情報取得
            model_info = self.client.show(self.active_model)
            
            # メモリ使用量に基づく最適化
            available_memory = self._get_available_memory_gb()
            
            if available_memory < 8:
                # メモリ不足時の軽量化設定
                self.max_tokens = min(self.max_tokens, 200)
                self.temperature = min(self.temperature, 0.5)
                logger.info("Applied low-memory optimizations")
            elif available_memory >= 16:
                # 高メモリ環境での高品質設定
                self.max_tokens = min(self.max_tokens, 500)
                logger.info("Applied high-memory optimizations")
            
        except Exception as e:
            logger.warning(f"Failed to optimize model settings: {e}")
    
    def _get_available_memory_gb(self) -> float:
        """利用可能メモリ量を取得（GB）"""
        try:
            import psutil
            return psutil.virtual_memory().available / (1024**3)
        except ImportError:
            return 8.0  # デフォルト値
    
    def generate_behavior_analysis(self, 
                                 behavior_data: Dict[str, Any],
                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """行動データから分析結果を生成 (最適化版)
        
        Args:
            behavior_data: 行動ログデータ
            context: 追加のコンテキスト情報
            
        Returns:
            dict: 分析結果
        """
        start_time = time.time()
        
        # フォールバックモードチェック
        if self.fallback_mode or self.active_model is None:
            logger.debug("Using fallback mode for behavior analysis")
            return {
                **self._generate_fallback_analysis(behavior_data),
                'from_cache': False,
                'fallback_mode': True,
                'processing_time_ms': (time.time() - start_time) * 1000
            }
        
        try:
            # Phase 3.2: キャッシュチェック
            cache_key = self._generate_cache_key('analysis', behavior_data, context)
            
            if self.cache_enabled:
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit for behavior analysis: {cache_key[:8]}...")
                    cached_result['from_cache'] = True
                    cached_result['processing_time_ms'] = (time.time() - start_time) * 1000
                    return cached_result
            
            prompt = self._create_behavior_analysis_prompt(behavior_data, context)
            
            # Phase 3.2: タイムアウト付き推論
            response = self._inference_with_timeout(
                model=self.active_model,
                messages=[
                    {
                        'role': 'system',
                        'content': self._get_behavior_analysis_system_prompt()
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens
                }
            )
            
            analysis_text = response['message']['content']
            
            # 構造化された分析結果を抽出
            analysis = self._parse_behavior_analysis(analysis_text)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = {
                'raw_analysis': analysis_text,
                'structured_analysis': analysis,
                'model_used': self.active_model,
                'timestamp': datetime.utcnow().isoformat(),
                'from_cache': False,
                'fallback_mode': False,
                'processing_time_ms': processing_time
            }
            
            # Phase 3.2: キャッシュに保存
            if self.cache_enabled:
                self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating behavior analysis: {e}")
            return {
                **self._generate_fallback_analysis(behavior_data),
                'error': str(e),
                'fallback_mode': True,
                'processing_time_ms': (time.time() - start_time) * 1000
            }
    
    def generate_advice(self, 
                       analysis_result: Dict[str, Any],
                       user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析結果からアドバイスを生成
        
        Args:
            analysis_result: 行動分析結果
            user_profile: ユーザープロファイル
            
        Returns:
            dict: アドバイス結果
        """
        start_time = time.time()
        
        # フォールバックモードチェック
        if self.fallback_mode or self.active_model is None:
            logger.debug("Using fallback mode for advice generation")
            return {
                **self._generate_fallback_advice(analysis_result),
                'fallback_mode': True,
                'processing_time_ms': (time.time() - start_time) * 1000
            }
        
        try:
            prompt = self._create_advice_generation_prompt(analysis_result, user_profile)
            
            response = self.client.chat(
                model=self.active_model,
                messages=[
                    {
                        'role': 'system',
                        'content': self._get_advice_generation_system_prompt()
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': self.temperature * 0.8,  # アドバイスは少し保守的に
                    'num_predict': 200
                }
            )
            
            advice_text = response['message']['content']
            
            # 構造化されたアドバイスを抽出
            advice = self._parse_advice_response(advice_text)
            
            return {
                'advice_text': advice_text,
                'structured_advice': advice,
                'priority': advice.get('priority', 'medium'),
                'emotion': advice.get('emotion', 'encouraging'),
                'model_used': self.active_model,
                'fallback_mode': False,
                'timestamp': datetime.utcnow().isoformat(),
                'processing_time_ms': (time.time() - start_time) * 1000
            }
            
        except Exception as e:
            logger.error(f"Error generating advice: {e}")
            return {
                **self._generate_fallback_advice(analysis_result),
                'error': str(e),
                'fallback_mode': True,
                'processing_time_ms': (time.time() - start_time) * 1000
            }
    
    def _create_behavior_analysis_prompt(self, 
                                       behavior_data: Dict[str, Any],
                                       context: Optional[Dict[str, Any]]) -> str:
        """行動分析用プロンプトを作成"""
        
        # 基本的な行動データの要約
        focus_level = behavior_data.get('focus_level', 'N/A')
        smartphone_detected = behavior_data.get('smartphone_detected', False)
        presence_status = behavior_data.get('presence_status', 'unknown')
        session_duration = behavior_data.get('session_duration_minutes', 0)
        
        prompt = f"""
以下の行動データを分析してください：

【基本情報】
- セッション時間: {session_duration}分
- 集中度レベル: {focus_level}
- スマートフォン使用: {'検出' if smartphone_detected else '未検出'}
- 在席状況: {presence_status}

【詳細データ】
{json.dumps(behavior_data, ensure_ascii=False, indent=2)}
"""
        
        if context:
            prompt += f"\n【追加コンテキスト】\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        
        prompt += """

この行動データから以下の観点で分析してください：
1. 集中度の傾向
2. 注意散漫の要因
3. 改善すべき行動パターン
4. ポジティブな行動の特定
"""
        
        return prompt
    
    def _create_advice_generation_prompt(self, 
                                       analysis_result: Dict[str, Any],
                                       user_profile: Optional[Dict[str, Any]]) -> str:
        """アドバイス生成用プロンプトを作成"""
        
        analysis = analysis_result.get('structured_analysis', {})
        
        prompt = f"""
以下の行動分析結果に基づいて、適切なアドバイスを生成してください：

【分析結果】
{json.dumps(analysis, ensure_ascii=False, indent=2)}
"""
        
        if user_profile:
            prompt += f"\n【ユーザープロファイル】\n{json.dumps(user_profile, ensure_ascii=False, indent=2)}"
        
        prompt += """

以下の要件でアドバイスを生成してください：
1. 親しみやすく、励ましの言葉を含める
2. 具体的で実行可能な提案をする
3. ユーザーの気持ちに寄り添う表現
4. 短く簡潔（音声再生を考慮）
5. 優先度レベル（high/medium/low）を判定
6. 適切な感情トーン（encouraging/gentle/alert）を選択
"""
        
        return prompt
    
    def _get_behavior_analysis_system_prompt(self) -> str:
        """行動分析用システムプロンプト"""
        return """あなたは学習・作業の行動分析の専門家です。

ユーザーの監視データから以下を分析してください：
- 集中度の傾向とパターン
- 注意散漫の要因
- 作業効率に影響する行動
- 改善可能な領域

分析は客観的で建設的なものにし、ユーザーの成長をサポートする視点で行ってください。
JSON形式での構造化された回答も含めて提供してください。"""
    
    def _get_advice_generation_system_prompt(self) -> str:
        """アドバイス生成用システムプロンプト"""
        return """あなたは優しく励ましながら学習をサポートするAIアシスタントです。

以下の特徴でアドバイスしてください：
- 親しみやすく温かい口調
- 具体的で実行しやすい提案
- ユーザーの努力を認める
- 短く分かりやすい表現（音声での再生を考慮）
- 適切な優先度と感情トーンの判定

ユーザーが前向きに取り組めるようなアドバイスを心がけてください。"""
    
    def _parse_behavior_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """分析テキストから構造化データを抽出"""
        
        # 基本的な構造化（将来的にはより精密なパースを実装）
        return {
            'analysis_summary': analysis_text[:200],  # 要約
            'focus_assessment': 'medium',  # デフォルト値
            'attention_issues': [],
            'positive_behaviors': [],
            'recommendations': []
        }
    
    def _parse_advice_response(self, advice_text: str) -> Dict[str, Any]:
        """アドバイステキストから構造化データを抽出"""
        
        # 優先度の推定（キーワードベース）
        priority = 'medium'
        if any(word in advice_text.lower() for word in ['緊急', '重要', '注意', '危険']):
            priority = 'high'
        elif any(word in advice_text.lower() for word in ['良い', '順調', '継続', '素晴らしい']):
            priority = 'low'
        
        # 感情トーンの推定
        emotion = 'encouraging'
        if any(word in advice_text.lower() for word in ['注意', '気をつけ', '改善']):
            emotion = 'gentle'
        elif any(word in advice_text.lower() for word in ['緊急', '危険']):
            emotion = 'alert'
        
        return {
            'priority': priority,
            'emotion': emotion,
            'main_message': advice_text[:100],  # メインメッセージ
            'action_items': []  # 実行すべき項目
        }
    
    def _generate_fallback_analysis(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック分析（LLMエラー時）"""
        focus_level = behavior_data.get('focus_level', 0.5)
        
        if focus_level >= 0.7:
            assessment = '良好な集中状態です'
        elif focus_level >= 0.4:
            assessment = '普通の集中状態です'
        else:
            assessment = '集中力が低下しています'
        
        return {
            'analysis_summary': assessment,
            'focus_assessment': 'medium',
            'fallback': True
        }
    
    def _generate_fallback_advice(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバックアドバイス（LLMエラー時）"""
        return {
            'advice_text': '少し休憩を取って、リフレッシュしてから作業を続けてみてください。',
            'priority': 'medium',
            'emotion': 'encouraging',
            'fallback': True
        }
    
    def health_check(self) -> Dict[str, Any]:
        """LLMサービスのヘルスチェック
        
        Returns:
            dict: ヘルスチェック結果
        """
        # フォールバックモードの場合
        if self.fallback_mode or self.active_model is None:
            return {
                'status': 'fallback_mode',
                'active_model': 'fallback_mode',
                'response_test': 'using_predefined_responses',
                'message': 'LLM service running in fallback mode',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            # 簡単なテスト推論
            response = self.client.chat(
                model=self.active_model,
                messages=[
                    {
                        'role': 'user',
                        'content': 'こんにちは'
                    }
                ],
                options={
                    'num_predict': 20
                }
            )
            
            return {
                'status': 'healthy',
                'active_model': self.active_model,
                'response_test': 'passed',
                'message': f'LLM service healthy with model: {self.active_model}',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Health check failed, switching to fallback mode: {e}")
            # ヘルスチェック失敗時にフォールバックモードに切り替え
            self._enable_fallback_mode()
            return {
                'status': 'error_fallback',
                'error': str(e),
                'active_model': 'fallback_mode',
                'message': 'Health check failed, switched to fallback mode',
                'timestamp': datetime.utcnow().isoformat()
            }

    # Phase 3.2: パフォーマンス最適化メソッド
    def _generate_cache_key(self, operation: str, *args) -> str:
        """キャッシュキーを生成
        
        Args:
            operation: 操作種別 ('analysis', 'advice')
            *args: ハッシュ対象のデータ
            
        Returns:
            str: キャッシュキー
        """
        content = f"{operation}:" + json.dumps(args, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """キャッシュからデータを取得
        
        Args:
            cache_key: キャッシュキー
            
        Returns:
            Optional[Dict]: キャッシュされたデータまたはNone
        """
        with self._cache_lock:
            cache_entry = self._response_cache.get(cache_key)
            
            if cache_entry:
                # TTL チェック
                cached_time = datetime.fromisoformat(cache_entry['cached_at'])
                if datetime.utcnow() - cached_time < timedelta(hours=self.cache_ttl):
                    return cache_entry['data']
                else:
                    # 期限切れのエントリを削除
                    del self._response_cache[cache_key]
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """データをキャッシュに保存
        
        Args:
            cache_key: キャッシュキー
            data: 保存するデータ
        """
        with self._cache_lock:
            # キャッシュサイズ制限（メモリ節約）
            if len(self._response_cache) > 100:
                # 古いエントリを削除（LRU風）
                oldest_key = min(
                    self._response_cache.keys(),
                    key=lambda k: self._response_cache[k]['cached_at']
                )
                del self._response_cache[oldest_key]
            
            self._response_cache[cache_key] = {
                'data': data,
                'cached_at': datetime.utcnow().isoformat()
            }
    
    def _inference_with_timeout(self, **kwargs) -> Dict[str, Any]:
        """タイムアウト付きLLM推論（スレッドセーフ版）
        
        Args:
            **kwargs: ollama.chat()に渡す引数
            
        Returns:
            Dict: 推論結果
            
        Raises:
            TimeoutError: タイムアウト時
        """
        # フォールバックモードチェック
        if self.fallback_mode or self.active_model is None:
            raise RuntimeError("LLM service is in fallback mode")
        
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
        import threading
        
        def inference_task():
            """推論実行タスク"""
            try:
                return self.client.chat(**kwargs)
            except Exception as e:
                logger.error(f"LLM inference task failed: {e}")
                raise e
        
        try:
            # スレッドセーフなタイムアウト処理
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix="llm_inference") as executor:
                future = executor.submit(inference_task)
                try:
                    response = future.result(timeout=self.inference_timeout)
                    logger.debug(f"LLM inference completed successfully")
                    return response
                except FutureTimeoutError:
                    logger.warning(f"LLM inference timeout after {self.inference_timeout}s")
                    # タイムアウト時のクリーンアップ
                    future.cancel()
                    raise TimeoutError(f"LLM inference timeout after {self.inference_timeout}s")
                    
        except Exception as e:
            if isinstance(e, TimeoutError):
                raise e
            else:
                logger.error(f"LLM inference error: {e}")
                raise e
    
    def clear_cache(self) -> int:
        """キャッシュをクリア
        
        Returns:
            int: クリアしたエントリ数
        """
        with self._cache_lock:
            count = len(self._response_cache)
            self._response_cache.clear()
            logger.info(f"Cleared {count} cache entries")
            return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得
        
        Returns:
            Dict: キャッシュ統計
        """
        with self._cache_lock:
            current_time = datetime.utcnow()
            valid_entries = 0
            
            for entry in self._response_cache.values():
                cached_time = datetime.fromisoformat(entry['cached_at'])
                if current_time - cached_time < timedelta(hours=self.cache_ttl):
                    valid_entries += 1
            
            return {
                'total_entries': len(self._response_cache),
                'valid_entries': valid_entries,
                'cache_hit_rate': getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1),
                'cache_ttl_hours': self.cache_ttl
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得
        
        Returns:
            Dict: パフォーマンス統計
        """
        memory_gb = self._get_available_memory_gb()
        
        return {
            'active_model': self.active_model,
            'fallback_mode': self.fallback_mode,
            'available_memory_gb': memory_gb,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'cache_enabled': self.cache_enabled,
            'inference_timeout_seconds': self.inference_timeout,
            'cache_stats': self.get_cache_stats() if not self.fallback_mode else {'status': 'disabled_in_fallback_mode'}
        } 