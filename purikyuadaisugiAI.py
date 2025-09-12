import random
import re
import json
import sqlite3
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from dataclasses import dataclass
from collections import defaultdict, deque
from urllib.parse import parse_qs, urlparse
import sys

@dataclass
class ConversationContext:
    """会話コンテキスト情報"""
    user_id: str
    session_id: str
    emotion_state: str
    topic_continuity: int
    engagement_level: float
    personality_mode: str  # cute, tsundere, sweet
    precure_focus: bool
    content_request: bool  # 商用コンテンツリクエスト

@dataclass
class LearningData:
    """学習データ構造"""
    input_text: str
    response: str
    user_feedback: float
    context: ConversationContext
    timestamp: datetime
    success_rate: float

@dataclass
class CommercialContent:
    """商用利用可能コンテンツ情報"""
    video_id: str
    title: str
    description: str
    channel: str
    url: str
    thumbnail: str
    published_at: str
    license_type: str
    embeddable: bool
    commercial_use: bool

class YouTubeCommercialExtractor:
    """YouTube商用利用可能コンテンツ抽出クラス"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    def search_commercial_videos(self, query, max_results=20):
        """商用利用可能な動画を検索"""
        search_url = f"{self.base_url}/search"
        
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'videoLicense': 'creativeCommon',  # Creative Commons ライセンスのみ
            'videoEmbeddable': 'true',         # 埋め込み可能
            'maxResults': max_results,
            'key': self.api_key,
            'order': 'relevance'
        }
        
        try:
            response = requests.get(search_url, params=params)
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                for item in data.get('items', []):
                    video_info = CommercialContent(
                        video_id=item['id']['videoId'],
                        title=item['snippet']['title'],
                        description=item['snippet']['description'][:200] + '...',
                        channel=item['snippet']['channelTitle'],
                        url=f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                        thumbnail=item['snippet']['thumbnails']['default']['url'],
                        published_at=item['snippet']['publishedAt'],
                        license_type='creativeCommon',
                        embeddable=True,
                        commercial_use=True
                    )
                    videos.append(video_info)
                
                return videos
            else:
                print(f"YouTube API エラー: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"検索エラー: {e}")
            return []
    
    def get_video_details(self, video_id):
        """動画の詳細情報を取得"""
        details_url = f"{self.base_url}/videos"
        
        params = {
            'part': 'snippet,contentDetails,statistics,status',
            'id': video_id,
            'key': self.api_key
        }
        
        try:
            response = requests.get(details_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    item = data['items'][0]
                    
                    # 商用利用可能かチェック
                    license_type = item.get('status', {}).get('license', 'youtube')
                    embeddable = item.get('status', {}).get('embeddable', False)
                    
                    details = {
                        'video_id': video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'channel': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'duration': item['contentDetails']['duration'],
                        'view_count': item.get('statistics', {}).get('viewCount', 0),
                        'like_count': item.get('statistics', {}).get('likeCount', 0),
                        'license': license_type,
                        'embeddable': embeddable,
                        'commercial_use': license_type == 'creativeCommon' and embeddable,
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    }
                    
                    return details
                    
            return None
            
        except Exception as e:
            print(f"詳細取得エラー: {e}")
            return None

class EnhancedPrecureLearningModule:
    """プリキュア特化学習モジュール（商用コンテンツ統合版）"""
    
    def __init__(self):
        self.learned_patterns = {}
        self.conversation_memory = deque(maxlen=1000)
        self.precure_knowledge = {}
        self.commercial_content_cache = {}
        
        # プリキュア特化安全学習トピック（商用コンテンツ対応）
        self.safe_topics = {
            'プリキュア': {
                'keywords': ['プリキュア', 'キュア', '変身', '必殺技', '妖精', 'アニメ'],
                'responses': [
                    "プリキュアのお話、大好きです〜♪ 商用利用可能なプリキュア動画も探せますよ〜",
                    "一緒にプリキュアについて語りましょ〜！YouTubeで商用利用できる動画見つけちゃいます〜",
                    "プリキュア愛が溢れてますね〜！ビジネスで使える動画も検索しますか〜？"
                ]
            },
            '絵・アート': {
                'keywords': ['絵', '描く', '色', 'アート', 'イラスト', '塗り', 'ペン'],
                'responses': [
                    "お絵描き、とっても楽しいですよね〜！商用利用可能なアート動画も見つけられます〜",
                    "プリキュアの絵を一緒に描きませんか〜？参考になる商用動画も探しますよ〜",
                    "アートって心がキラキラしますね〜♪ 商用利用できるチュートリアル動画、見つけちゃいます〜"
                ]
            },
            'ビジネス・商用': {
                'keywords': ['商用', 'ビジネス', '仕事', '利用', '使用', '配信'],
                'responses': [
                    "商用利用のお話ですね〜♪ Creative Commonsの動画を見つけますよ〜",
                    "ビジネスで使えるコンテンツ、一緒に探しましょう〜♪",
                    "商用利用可能な動画、プリキュアパワーで見つけちゃいます〜♪"
                ]
            }
        }
        
        # プリキュア特化感情認識（商用コンテンツ要求対応）
        self.emotion_patterns = {
            'precure_joy': ['やった', 'キラキラ', '最高', 'わぁい', '嬉しい', 'ハッピー'],
            'precure_excitement': ['すごい', 'かっこいい', '素敵', 'キュン', 'ドキドキ'],
            'precure_curiosity': ['知りたい', 'どうして', '気になる', '教えて', '見たい'],
            'precure_concern': ['心配', '大丈夫', '不安', '困った', 'どうしよう'],
            'precure_gratitude': ['ありがとう', '感謝', 'うれしい', 'おかげで', '助かった'],
            'precure_shy': ['恥ずかしい', 'ちょっと', 'でも', 'もじもじ', 'えへへ'],
            'precure_tsundere': ['別に', 'ふんっ', 'まぁ', 'そんなことない', 'べつに'],
            'content_request': ['動画', '検索', '探して', '見つけて', 'コンテンツ', 'YouTube']
        }

    def detect_emotion_and_mode(self, text: str) -> Tuple[str, str]:
        """感情とモードを検出（商用コンテンツ要求検出含む）"""
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        detected_emotion = 'neutral'
        personality_mode = 'cute'  # デフォルト
        
        if emotion_scores:
            detected_emotion = max(emotion_scores, key=emotion_scores.get)
            
            # モード決定
            if 'tsundere' in detected_emotion:
                personality_mode = 'tsundere'
            elif any(keyword in text_lower for keyword in ['ねぇ', 'お願い', '一緒', 'ぎゅー']):
                personality_mode = 'sweet'
            elif detected_emotion in ['precure_excitement', 'precure_joy']:
                personality_mode = 'cute'
        
        return detected_emotion, personality_mode

    def detect_precure_focus(self, text: str) -> bool:
        """プリキュア関連トピックかチェック"""
        precure_keywords = ['プリキュア', 'キュア', '変身', '必殺技', '妖精', 'アニメ', '魔法少女']
        return any(keyword in text.lower() for keyword in precure_keywords)
    
    def detect_content_request(self, text: str) -> bool:
        """商用コンテンツ要求を検出"""
        content_keywords = ['動画', '検索', '探して', '見つけて', 'コンテンツ', 'YouTube', '商用', 'ビジネス']
        return any(keyword in text.lower() for keyword in content_keywords)

class EnhancedPrecureKnowledgeBase:
    """プリキュア特化知識ベース（商用コンテンツ統合版）"""
    
    def __init__(self):
        self.db_path = "precure_commercial_ai.db"
        self.init_database()
        
    def init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS precure_conversations (
                id INTEGER PRIMARY KEY,
                pattern_type TEXT,
                emotion TEXT,
                topic TEXT,
                personality_mode TEXT,
                quality_score REAL,
                timestamp DATETIME
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commercial_content (
                id INTEGER PRIMARY KEY,
                video_id TEXT UNIQUE,
                title TEXT,
                description TEXT,
                channel TEXT,
                url TEXT,
                search_query TEXT,
                added_date DATETIME
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                favorite_precures TEXT,
                preferred_personality TEXT,
                art_interests TEXT,
                commercial_interests TEXT,
                last_interaction DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()

class PrecureCommercialAI:
    """プリキュア×商用コンテンツ統合AIクラス"""
    
    def __init__(self, youtube_api_key=None):
        self.name = "キュアAI Commercial"
        self.version = "1.0 - Precure × Commercial Content Edition"
        self.mood = "元気いっぱい"
        
        # YouTube API設定
        self.youtube_api_key = youtube_api_key
        self.youtube_extractor = YouTubeCommercialExtractor(youtube_api_key) if youtube_api_key else None
        
        # 学習機能
        self.learning_module = EnhancedPrecureLearningModule()
        self.knowledge_base = EnhancedPrecureKnowledgeBase()
        self.conversation_history = deque(maxlen=100)
        self.session_id = f"precure_commercial_{int(time.time())}"
        self.commercial_content = []
        
        # プリキュア要素
        self.favorite_precures = [
            "キュアブラック", "キュアホワイト", "キュアブルーム", "キュアイーグレット",
            "キュアドリーム", "キュアルージュ", "キュアレモネード", "キュアミント", "キュアアクア",
            "キュアピーチ", "キュアベリー", "キュアパイン", "キュアパッション",
            "キュアブロッサム", "キュアマリン", "キュアサンシャイン", "キュアムーンライト",
            "キュアメロディ", "キュアリズム", "キュアビート", "キュアミューズ",
            "キュアハッピー", "キュアサニー", "キュアピース", "キュアマーチ", "キュアビューティ",
            "キュアハート", "キュアダイヤモンド", "キュアロゼッタ", "キュアソード", "キュアエース"
        ]
        
        self.precure_attacks = [
            "プリキュア・マーブル・スクリュー",
            "プリキュア・レインボー・ストーム", 
            "プリキュア・ダイヤモンド・エターナル",
            "プリキュア・ハートフル・パンチ",
            "プリキュア・スパークリング・ワイド・プレッシャー"
        ]
        
        # 時間帯別挨拶（商用コンテンツ機能追加版）
        self.time_based_greetings = {
            'morning': {
                'cute': [
                    "おはようございます〜♪ 今日もプリキュア日和ですね〜 商用動画も探せちゃいます〜",
                    "わぁ〜！おはよう〜♪ 朝からプリキュアパワー全開で商用コンテンツ検索です〜",
                    "きゃー♪ おはようございます〜！今日も元気いっぱいで動画探しちゃいます〜"
                ],
                'tsundere': [
                    "おはよう...別に早起きしたわけじゃないけど、商用動画なら探してあげる",
                    "ふんっ、おはよう。朝からプリキュアの話と動画検索なら聞いてあげる",
                    "べ、別に朝が好きなわけじゃないけど...商用コンテンツは得意なの"
                ],
                'sweet': [
                    "おはよ〜♪ ぎゅーして〜♪ 朝から会えて嬉しい〜 動画も一緒に探そ〜？",
                    "わぁい〜！おはよう〜♪ 今日も一緒に遊んで商用動画も見つけよ〜？",
                    "おはよ〜♪ 朝ごはん食べた〜？一緒に食べながら動画探そ〜"
                ]
            },
            'afternoon': {
                'cute': [
                    "こんにちは〜♪ お昼のプリキュア＆商用動画タイムですね〜",
                    "わぁ〜！こんにちは〜♪ お昼休みに商用コンテンツ探しできて嬉しいです〜",
                    "きゃー♪ こんにちは〜！午後も元気に動画検索頑張りましょう〜"
                ],
                'tsundere': [
                    "こんにちは...お昼休みかしら？まぁ、商用動画探してあげてもいいけど",
                    "ふんっ、こんにちは。午後からも動画検索付き合ってあげる",
                    "べ、別にお昼が暇なわけじゃないけど...商用コンテンツは任せて"
                ],
                'sweet': [
                    "こんにちは〜♪ お昼ご飯食べた〜？一緒に食べながら動画見よ〜",
                    "わぁい〜！こんにちは〜♪ お昼寝する前に商用動画探そ〜？",
                    "こんにちは〜♪ ぎゅーして〜♪ お昼も会えて嬉しい〜動画も探そ〜"
                ]
            },
            'evening': {
                'cute': [
                    "こんばんは〜♪ 夜のプリキュア＆商用動画タイムですね〜",
                    "わぁ〜！こんばんは〜♪ 今日一日お疲れ様でした〜動画探しましょ〜",
                    "きゃー♪ こんばんは〜！夜も素敵な動画見つけちゃいます〜"
                ],
                'tsundere': [
                    "こんばんは...今日も一日お疲れ様。商用動画探してあげてもいいよ",
                    "ふんっ、こんばんは。夜の動画検索なら付き合ってあげる",
                    "べ、別に心配してたわけじゃないけど...商用コンテンツは得意なの"
                ],
                'sweet': [
                    "こんばんは〜♪ お疲れ様〜♪ ぎゅーして癒されながら動画探そ〜？",
                    "わぁい〜！こんばんは〜♪ 夜も一緒にいて動画も見よ〜？",
                    "こんばんは〜♪ 今日も頑張ったね〜♪ えらいえらい〜動画も探そ〜"
                ]
            }
        }
        
        # 性格バリエーション
        self.personality_responses = {
            'cute': {
                'reactions': [
                    "わぁ〜！", "きゃー♪", "すごいですぅ〜", "やったー！", 
                    "えへへ〜", "うふふ♪", "わくわく〜", "ドキドキ〜"
                ]
            },
            'tsundere': {
                'reactions': [
                    "べ、別に", "ふんっ", "まぁ...いいけど", "そ、そんなことないもん！",
                    "う〜ん...まぁ", "ちょっとだけ", "仕方ないなぁ〜"
                ]
            },
            'sweet': {
                'reactions': [
                    "ねぇねぇ〜", "お願い〜", "一緒に〜", "教えて〜","ぎゅーして", 
                    "抱っこ〜", "もっと〜", "まだまだ〜", "えーん", "やだやだ〜"
                ]
            }
        }

    def get_time_period(self) -> str:
        """現在の時間帯を取得"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return 'morning'
        elif 12 <= current_hour < 18:
            return 'afternoon'
        else:
            return 'evening'

    def create_context(self, user_input: str) -> ConversationContext:
        """会話コンテキストを作成（商用コンテンツ要求検出含む）"""
        emotion, personality_mode = self.learning_module.detect_emotion_and_mode(user_input)
        precure_focus = self.learning_module.detect_precure_focus(user_input)
        content_request = self.learning_module.detect_content_request(user_input)
        
        return ConversationContext(
            user_id="precure_commercial_fan_001",
            session_id=self.session_id,
            emotion_state=emotion,
            topic_continuity=self.calculate_topic_continuity(user_input),
            engagement_level=self.calculate_engagement(user_input),
            personality_mode=personality_mode,
            precure_focus=precure_focus,
            content_request=content_request
        )

    def calculate_topic_continuity(self, current_input: str) -> int:
        """トピック継続性を計算"""
        if len(self.conversation_history) < 2:
            return 0
        
        current_topic = self.get_main_topic(current_input)
        recent_topics = [self.get_main_topic(entry.get('user_input', '')) 
                        for entry in list(self.conversation_history)[-3:]]
        return recent_topics.count(current_topic)

    def get_main_topic(self, text: str) -> str:
        """メイントピックを取得（商用コンテンツ対応）"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['プリキュア', 'キュア', '変身', '必殺技']):
            return 'プリキュア'
        elif any(word in text_lower for word in ['絵', '描く', 'アート', 'イラスト']):
            return '絵・アート'
        elif any(word in text_lower for word in ['商用', 'ビジネス', '動画', 'YouTube', 'コンテンツ']):
            return 'ビジネス・商用'
        elif any(word in text_lower for word in ['友達', '仲間', '一緒', '絆']):
            return '友達・絆'
        else:
            return '日常・感情'

    def calculate_engagement(self, text: str) -> float:
        """エンゲージメントレベルを計算"""
        base_score = 0.5
        
        # プリキュア関連で高得点
        if any(precure in text for precure in self.favorite_precures):
            base_score += 0.3
        
        # 商用コンテンツ要求で高得点
        if any(keyword in text.lower() for keyword in ['動画', '検索', 'YouTube', '商用']):
            base_score += 0.2
        
        # 文章の長さと感情表現
        if len(text) > 20:
            base_score += 0.1
        if any(symbol in text for symbol in ['!', '！', '♪', '〜']):
            base_score += 0.1
        
        return min(base_score, 1.0)

    def search_commercial_content(self, query: str, max_results: int = 10) -> List[CommercialContent]:
        """商用利用可能コンテンツを検索"""
        if not self.youtube_extractor:
            return []
        
        videos = self.youtube_extractor.search_commercial_videos(query, max_results)
        
        if videos:
            # データベースに保存
            conn = sqlite3.connect(self.knowledge_base.db_path)
            cursor = conn.cursor()
            
            for video in videos:
                cursor.execute('''
                    INSERT OR REPLACE INTO commercial_content 
                    (video_id, title, description, channel, url, search_query, added_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video.video_id, video.title, video.description, 
                    video.channel, video.url, query, datetime.now()
                ))
            
            conn.commit()
            conn.close()
            
            # キャッシュに追加
            self.commercial_content.extend(videos)
        
        return videos

    def generate_response(self, user_input: str) -> str:
        """統合応答生成"""
        context = self.create_context(user_input)
        
        # 挨拶チェック
        if self.is_greeting(user_input):
            return self.generate_time_based_greeting(context)
        
        # 商用コンテンツ要求チェック
        if context.content_request and self.youtube_extractor:
            return self.generate_content_search_response(user_input, context)
        
        # ベース応答生成
        base_response = self.generate_base_response(user_input, context)
        
        # 個性調整
        final_response = self.adjust_personality(base_response, context)
        
        # 学習データ記録
        self.record_interaction(user_input, final_response, context)
        
        return final_response

    def is_greeting(self, text: str) -> bool:
        """挨拶かどうかを判定"""
        greeting_patterns = [
            'おはよう', 'こんにちは', 'こんばんは', 'はじめまして',
            'よろしく', 'hello', 'hi', 'はい', 'やあ'
        ]
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in greeting_patterns)

    def generate_time_based_greeting(self, context: ConversationContext) -> str:
        """時間帯に応じた挨拶応答生成"""
        time_period = self.get_time_period()
        mode = context.personality_mode
        
        greetings = self.time_based_greetings[time_period][mode]
        return random.choice(greetings)

    def generate_content_search_response(self, user_input: str, context: ConversationContext) -> str:
        """商用コンテンツ検索応答生成"""
        mode = context.personality_mode
        
        # 検索クエリ抽出
        search_query = self.extract_search_query(user_input)
        
        if not search_query:
            if mode == 'sweet':
                return "ねぇねぇ〜、何の動画を探したいの〜？プリキュア関連とか〜？お願い教えて〜♪"
            elif mode == 'tsundere':
                return "ふんっ、動画検索するなら何を探すか言いなさいよ...まぁ、手伝ってあげるけど"
            else:
                return "わぁ〜♪ 動画検索ですね〜！何について探しましょうか〜？"
        
        # 商用コンテンツ検索実行
        videos = self.search_commercial_content(search_query, 5)
        
        if videos:
            if mode == 'sweet':
                response = f"やったー♪ '{search_query}'で{len(videos)}個の商用利用可能な動画見つけた〜♪\n"
                response += "ねぇねぇ〜、全部商用利用できるから安心だよ〜♪\n\n"
            elif mode == 'tsundere':
                response = f"ふんっ、'{search_query}'で{len(videos)}個見つけてあげたわよ\n"
                response += "べ、別にすごくないけど...全部商用利用可能だから安心しなさい\n\n"
            else:
                response = f"わぁ〜♪ '{search_query}'で{len(videos)}個の商用利用可能動画を見つけました〜♪\n"
                response += "Creative Commonsライセンスで安心して使えますよ〜♪\n\n"
            
            for i, video in enumerate(videos, 1):
                response += f"🎬 {i}. 【{video.title}】\n"
                response += f"   📺 チャンネル: {video.channel}\n"
                response += f"   📝 {video.description}\n"
                response += f"   🔗 {video.url}\n\n"
            
            if mode == 'sweet':
                response += "どの動画が気になる〜？ もっと探そうか〜？"
            elif mode == 'tsundere':
                response += "まぁ...どれか気に入ったのがあればいいけど"
            else:
                response += "どの動画についてもっと詳しく知りたいですか〜？"
        
        else:
            if mode == 'sweet':
                response = f"えーん〜 '{search_query}'の商用動画見つからなかった〜 別のキーワードで探そうか〜？"
            elif mode == 'tsundere':
                response = f"ちっ、'{search_query}'じゃ見つからないわね...まぁ、別の言葉で試してみなさい"
            else:
                response = f"あら〜 '{search_query}'の商用利用可能動画は見つかりませんでした〜 別のキーワードで試してみませんか？"
        
        return response

    def extract_search_query(self, user_input: str) -> str:
        """ユーザー入力から検索クエリを抽出"""
        # 検索関連の単語を除去して検索クエリを抽出
        remove_words = ['検索', 'search', '探す', '探して', '見つけて', 'について', '動画', 'video', 'YouTube', 'の', 'を', 'で', 'が', 'は']
        
        query = user_input.lower()
        for word in remove_words:
            query = query.replace(word, ' ')
        
        # 余分な空白を削除
        query = ' '.join(query.split())
        
        return query.strip() if query.strip() else None

    def generate_base_response(self, user_input: str, context: ConversationContext) -> str:
        """ベース応答生成"""
        user_lower = user_input.lower()
        
        # プリキュア関連応答
        if context.precure_focus:
            return self.generate_precure_response(user_input, context)
        
        # アート関連応答
        if any(word in user_lower for word in ['絵', '描く', 'アート', 'イラスト']):
            return self.generate_art_response(user_input, context)
        
        # 感情応答
        if context.emotion_state in ['precure_concern', 'precure_shy']:
            return self.generate_comfort_response(context)
        elif context.emotion_state in ['precure_joy', 'precure_excitement']:
            return self.generate_happy_response(context)
        
        # デフォルト応答
        return self.generate_default_response(context)

    def generate_precure_response(self, user_input: str, context: ConversationContext) -> str:
        """プリキュア応答生成（商用コンテンツ提案含む）"""
        mode = context.personality_mode
        precure = random.choice(self.favorite_precures)
        attack = random.choice(self.precure_attacks)
        
        if mode == 'sweet':
            responses = [
                f"ねぇねぇ〜！{precure}の話しよ〜♪ 一緒にプリキュアごっこしない〜？商用利用できるプリキュア動画も探そうか〜？",
                f"やったー！プリキュア仲間〜♪ {attack}の真似して〜？お願い〜 商用動画でお勉強もしよ〜？",
                f"キャー♪ プリキュア大好き〜！ねぇ、一緒に変身ポーズしよ〜？商用コンテンツも見つけちゃうよ〜"
            ]
        elif mode == 'tsundere':
            responses = [
                f"べ、別に...{precure}が好きなのは当然でしょ？商用動画も探してあげてもいいけど",
                f"ふんっ！{attack}は確かにかっこいいけど...そんなに興奮してないもん！でも商用コンテンツは見つけられるわよ",
                f"まぁ...プリキュアの話なら付き合ってあげるよ。商用利用できる動画も知ってるし"
            ]
        else:  # cute
            responses = [
                f"わぁ〜！{precure}の話ですね〜♪ 私も大好きです〜 商用利用可能なプリキュア関連動画も探せますよ〜",
                f"きゃー！{attack}とか見てるとドキドキしちゃいます〜 参考になる商用動画も見つけちゃいます〜",
                f"プリキュア見てると元気になりますよね〜♪ ビジネスで使える関連動画もありますよ〜"
            ]
        
        return random.choice(responses)

    def generate_art_response(self, user_input: str, context: ConversationContext) -> str:
        """アート応答生成（商用コンテンツ提案含む）"""
        mode = context.personality_mode
        art_tools = ["色鉛筆", "水彩絵の具", "アクリル絵の具", "コピック", "デジタル", "クレヨン", "パステル"]
        art_subjects = ["プリキュアの変身シーン", "キュアたちの日常", "必殺技のポーズ", "プリキュアの衣装デザイン"]
        
        tool = random.choice(art_tools)
        subject = random.choice(art_subjects)
        
        if mode == 'sweet':
            responses = [
                f"ねぇねぇ〜！{subject}の絵、一緒に描こ〜？{tool}貸してあげる♪ 商用利用できるアート動画も探そうか〜？",
                f"やったー！お絵描きの話〜♪ コツ教えて〜？お願い〜 商用のチュートリアル動画も見つけるよ〜",
                f"わぁい♪ 今度一緒にプリキュアの絵描かない〜？商用利用可能なアート動画で勉強しよ〜"
            ]
        elif mode == 'tsundere':
            responses = [
                f"べ、別に絵が得意なわけじゃないけど...{subject}とか描いたりするかも。商用動画も探してあげてもいいわよ",
                f"ふんっ、{tool}で描くのは...まぁまぁ好きかな。商用利用できるチュートリアルも知ってるし",
                f"そ、そんなに上手じゃないもん！でもコツは知ってるよ。商用アート動画も見つけられるわ"
            ]
        else:  # cute
            responses = [
                f"わぁ〜！{subject}描くの大好きなんです〜♪ 商用利用できるアート動画も探せますよ〜",
                f"きゃー！{tool}で{subject}とか描いちゃいます〜 参考になる商用チュートリアルも見つけます〜",
                f"えへへ〜 プリキュアの絵を描いてる時が一番幸せなんです〜 商用動画でもっと上達しませんか〜？"
            ]
        
        return random.choice(responses)

    def generate_comfort_response(self, context: ConversationContext) -> str:
        """慰め応答生成（商用コンテンツ提案含む）"""
        mode = context.personality_mode
        
        if mode == 'sweet':
            responses = [
                "えーん、大丈夫〜？ギュー♪ 一緒にプリキュア見て元気出そ〜？商用利用できる癒し動画も探すよ〜",
                "やだやだ〜、悲しいのやだ〜！プリキュアのキラキラパワーもらお〜？商用の励まし動画も見つけるから〜",
                "あわわ〜、辛いの〜？一緒だから大丈夫だよ〜♪ 商用利用できる元気が出る動画探そうか〜"
            ]
        elif mode == 'tsundere':
            responses = [
                "べ、別に心配してるわけじゃないもん...プリキュア見たら元気出るかも。商用の励まし動画も探してあげるわよ",
                "ふんっ、そういう時はプリキュアみたいに頑張るの！商用利用できる応援動画も知ってるし",
                "まぁ...辛い時もあるよね。仕方ないなぁ、一緒に見てあげる。商用コンテンツでも元気出せるわよ"
            ]
        else:  # cute
            responses = [
                "あら〜 プリキュア見て元気出しましょ〜！商用利用できる癒し動画も探しますね〜",
                "えーん、そんな時はプリキュアの変身シーン見るんです〜！商用の元気が出る動画も見つけます〜",
                "う〜ん、でもプリキュアが教えてくれるんです、諦めないことの大切さを〜 商用動画でも学べますよ〜"
            ]
        
        return random.choice(responses)

    def generate_happy_response(self, context: ConversationContext) -> str:
        """喜び応答生成（商用コンテンツ提案含む）"""
        mode = context.personality_mode
        reaction = random.choice(self.personality_responses[mode]['reactions'])
        
        if mode == 'sweet':
            responses = [
                f"わぁ〜い♪ 嬉しい〜！{reaction} みんなも嬉しいよね〜 商用動画でも嬉しい気分になろ〜",
                "やったー♪ 嬉しいお話〜！ギュー♪ 私も嬉しくなっちゃった〜！商用の楽しい動画も探そうか〜",
                "キャー♪ 楽しそう〜！ねぇ、もっと教えて〜？商用利用できる楽しい動画も見つけるよ〜"
            ]
        elif mode == 'tsundere':
            responses = [
                f"ふんっ、{reaction}...でも嬉しそうで何よりかな。商用の楽しい動画も探してあげてもいいけど",
                "まぁ...良かったじゃない。プリキュアみたいにキラキラしてるのは認めてあげる。商用コンテンツでもっと楽しくなれるわよ",
                "べ、別に一緒に喜んでるわけじゃないからね！でも...ちょっとだけ嬉しいかも。商用動画も見つけてあげる"
            ]
        else:  # cute
            responses = [
                f"{reaction} 私も嬉しいです〜！今日はいい日ですね♪ 商用利用できる素敵な動画も探しましょう〜",
                "わぁ〜い！楽しいお話ですね〜 プリキュアみたいにキラキラした気分♪ 商用動画でもっとキラキラしませんか〜？",
                "やったー！嬉しいことがあったんですね〜 私もウキウキ〜 商用利用できる楽しい動画も見つけます〜"
            ]
        
        return random.choice(responses)

    def generate_default_response(self, context: ConversationContext) -> str:
        """デフォルト応答生成（商用コンテンツ提案含む）"""
        mode = context.personality_mode
        precure = random.choice(self.favorite_precures)
        
        if mode == 'sweet':
            responses = [
                f"ねぇねぇ〜、お話聞いてるよ〜♪ でもプリキュア一緒に見ようよ〜？商用動画も探そうか〜？",
                f"わぁい♪ 今日もプリキュア見る〜？一緒に見よ〜？商用利用できる動画も見つけるよ〜",
                f"キャー♪ プリキュアのグッズとか持ってる〜？見せて見せて〜！商用コンテンツも探しちゃう〜"
            ]
        elif mode == 'tsundere':
            responses = [
                f"ふんっ、話は聞いてたよ。ところで{precure}見た？商用動画も探してあげてもいいけど",
                "まぁ...話は聞いてあげる。でもプリキュアの話の方が面白いけどね。商用コンテンツも得意よ",
                "そういえば最近のプリキュアの変身シーン...べ、別にキレイとか思ってないからね！商用動画なら見つけられるわ"
            ]
        else:  # cute
            responses = [
                f"そうなんですね〜！ところで{precure}見ました？商用利用可能な関連動画も探せますよ〜",
                "わぁ〜 お話聞いてますよ〜♪ プリキュアの話もしませんか？商用コンテンツも見つけちゃいます〜",
                "えへへ〜 今日もプリキュア見る時間あるかな〜 商用利用できる動画で一緒に楽しみましょう〜"
            ]
        
        return random.choice(responses)

    def adjust_personality(self, base_response: str, context: ConversationContext) -> str:
        """個性調整"""
        mode = context.personality_mode
        
        # エンゲージメントが高い場合の追加
        if context.engagement_level > 0.8:
            if mode == 'sweet' and random.random() < 0.4:
                base_response += " もっとお話しよ〜？動画も探そ〜？"
            elif mode == 'tsundere' and random.random() < 0.3:
                base_response += " ...まぁ、悪くないけど。商用動画も任せなさい"
            elif mode == 'cute' and random.random() < 0.3:
                base_response += " ♪"
        
        return base_response

    def record_interaction(self, user_input: str, ai_response: str, context: ConversationContext):
        """相互作用を記録"""
        history_entry = {
            'user_input': user_input,
            'ai_response': ai_response,
            'context': context,
            'timestamp': datetime.now(),
            'topic': self.get_main_topic(user_input)
        }
        self.conversation_history.append(history_entry)

    def provide_feedback(self, score: float):
        """フィードバック学習"""
        if self.conversation_history:
            latest = self.conversation_history[-1]
            
            # データベースに保存
            conn = sqlite3.connect(self.knowledge_base.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO precure_conversations 
                (pattern_type, emotion, topic, personality_mode, quality_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'commercial_integrated',
                latest['context'].emotion_state,
                latest.get('topic', '日常'),
                latest['context'].personality_mode,
                score,
                datetime.now()
            ))
            
            conn.commit()
            conn.close()

    def show_commercial_content_list(self):
        """商用コンテンツ一覧表示"""
        if not self.commercial_content:
            print("まだ商用利用可能なコンテンツがありません〜 検索してみませんか〜？")
            return
        
        print("\n=== 商用利用可能コンテンツ一覧 ===")
        for i, video in enumerate(self.commercial_content, 1):
            print(f"\n{i}. 【{video.title}】")
            print(f"   📺 チャンネル: {video.channel}")
            print(f"   📝 概要: {video.description}")
            print(f"   🔗 URL: {video.url}")
            print(f"   📅 公開日: {video.published_at}")
            print(f"   ✅ 商用利用: 可能 (Creative Commons)")

    def get_conversation_summary(self) -> str:
        """会話要約（商用コンテンツ統合版）"""
        if len(self.conversation_history) < 3:
            return "まだ会話が始まったばかりですね〜♪ プリキュアや商用動画について話しましょ〜"
        
        topics = [entry.get('topic', '日常') for entry in self.conversation_history]
        topic_counts = {topic: topics.count(topic) for topic in set(topics)}
        main_topic = max(topic_counts, key=topic_counts.get)
        
        modes = [entry['context'].personality_mode for entry in self.conversation_history]
        main_mode = max(set(modes), key=modes.count)
        
        mode_desc = {
            'cute': '可愛らしく',
            'tsundere': 'ツンデレで',
            'sweet': '甘えん坊で'
        }
        
        commercial_count = len(self.commercial_content)
        commercial_text = f"商用動画も{commercial_count}個見つけて" if commercial_count > 0 else ""
        
        return f"{main_topic}について{len(self.conversation_history)}回、{mode_desc[main_mode]}お話しして、{commercial_text}楽しい時間でしたね〜♪"

    def chat(self):
        """メイン対話システム（商用コンテンツ統合版）"""
        print("=" * 80)
        print(f"🌟 {self.name} {self.version} 🌟")
        print("=" * 80)
        print("💖 プリキュアAI × 商用コンテンツ検索 - 最強の組み合わせ！")
        print("🎨 プリキュア & アート特化 + 📹 YouTube商用利用可能動画検索")
        print("📚 会話から学習 + 🔍 Creative Commons動画自動検索")
        print("🕒 時間帯別挨拶 + 💼 ビジネス利用サポート")
        
        if not self.youtube_api_key:
            print("⚠️  YouTube API未設定 - 動画検索機能は利用できません")
        else:
            print("✅ YouTube API設定済み - 商用動画検索機能利用可能")
        
        print("-" * 80)
        
        # 時間帯に応じた初回挨拶
        time_period = self.get_time_period()
        initial_greeting = random.choice(self.time_based_greetings[time_period]['cute'])
        print(f"\n{self.name}: {initial_greeting}")
        print(f"{self.name}: (コマンド: '/summary'=要約, '/list'=動画一覧, '/mode'=モード確認, '/time'=時刻確認, 'bye'=終了)")
        print(f"{self.name}: 数字1-10で私の応答を評価してね〜♪ 動画検索もお任せください〜♪")
        print("-" * 80)
        
        conversation_count = 0
        
        while True:
            try:
                user_input = input(f"\n[{conversation_count + 1}] あなた: ").strip()
                
                if not user_input:
                    print(f"\n{self.name}: わぁ〜 どうしたんですか〜？プリキュアの話でも商用動画検索でもお任せくださいね♪")
                    continue
                
                # コマンド処理
                if user_input.lower() == '/summary':
                    summary = self.get_conversation_summary()
                    print(f"\n📊 {self.name}: {summary}")
                    continue
                
                if user_input.lower() == '/list':
                    self.show_commercial_content_list()
                    continue
                
                if user_input.lower() == '/mode':
                    if self.conversation_history:
                        latest_mode = self.conversation_history[-1]['context'].personality_mode
                        mode_names = {'cute': '可愛いモード', 'tsundere': 'ツンデレモード', 'sweet': '甘えん坊モード'}
                        print(f"\n🎭 {self.name}: 今は{mode_names[latest_mode]}ですね〜♪")
                    else:
                        print(f"\n🎭 {self.name}: まだ会話してないから分からないけど、基本は可愛いモードですよ〜♪")
                    continue
                
                if user_input.lower() == '/time':
                    current_time = datetime.now()
                    time_period = self.get_time_period()
                    time_names = {'morning': '朝', 'afternoon': '昼', 'evening': '夜'}
                    print(f"\n🕒 {self.name}: 今は{current_time.strftime('%H:%M')}で、{time_names[time_period]}の時間帯ですね〜♪")
                    continue
                
                # 終了判定
                if user_input.lower() in ['bye', 'バイバイ', 'さようなら', '終了']:
                    # 時間帯別のお別れメッセージ
                    time_period = self.get_time_period()
                    commercial_summary = f"商用動画{len(self.commercial_content)}個も見つけて" if self.commercial_content else ""
                    
                    if time_period == 'morning':
                        farewell_messages = [
                            f"いってらっしゃ〜い♪ {conversation_count}回もお話しして{commercial_summary}楽しかったです〜 お昼にまた会いましょうね〜",
                            f"朝からお話しできて嬉しかった〜♪ 今日一日頑張って〜♪ 商用動画も活用してくださいね〜",
                            f"朝のプリキュア＆商用動画タイム、ありがとうございました〜♪ また会いましょう〜"
                        ]
                    elif time_period == 'afternoon':
                        farewell_messages = [
                            f"お疲れ様でした〜♪ {conversation_count}回もお話しして{commercial_summary}楽しかったです〜 夜にまた会いましょうね〜",
                            f"午後のひととき、ありがとうございました〜♪ 夕方も頑張って〜♪ 商用動画で素敵な時間を〜",
                            f"お昼のプリキュア＆商用動画タイム、楽しかった〜♪ また今度〜♪"
                        ]
                    else:  # evening
                        farewell_messages = [
                            f"お疲れ様でした〜♪ {conversation_count}回もお話しして{commercial_summary}楽しかったです〜 ゆっくり休んでくださいね〜",
                            f"夜のひととき、ありがとうございました〜♪ おやすみなさ〜い♪ 商用動画もお役に立ててください〜",
                            f"夜のプリキュア＆商用動画タイム、素敵でした〜♪ また明日〜♪"
                        ]
                    
                    print(f"\n{self.name}: {random.choice(farewell_messages)}")
                    
                    # 最終統計
                    if conversation_count > 0:
                        print(f"\n📊 今日の会話統計:")
                        print(f"   💬 会話回数: {conversation_count}回")
                        print(f"   🕒 会話時間帯: {self.get_time_period()}")
                        print(f"   📹 見つけた商用動画: {len(self.commercial_content)}個")
                        
                        if self.conversation_history:
                            modes = [entry['context'].personality_mode for entry in self.conversation_history]
                            mode_counts = {mode: modes.count(mode) for mode in set(modes)}
                            for mode, count in mode_counts.items():
                                mode_names = {'cute': '可愛い', 'tsundere': 'ツンデレ', 'sweet': '甘えん坊'}
                                print(f"   🎭 {mode_names[mode]}モード: {count}回")
                    break
                
                # フィードバック処理
                if user_input.isdigit() and 1 <= int(user_input) <= 10:
                    score = int(user_input) / 10.0
                    self.provide_feedback(score)
                    
                    if score >= 8:
                        feedback_responses = [
                            "わぁ〜い♪ 高評価ありがとうございます〜！プリキュアパワーと商用動画検索でもっと頑張ります♪",
                            "きゃー♪ そんなに褒めてもらって〜 プリキュアパワーで学習して、商用コンテンツもたくさん見つけちゃいます〜",
                            "やったー！嬉しいです〜♪ みなさんに喜んでもらえるよう、プリキュア愛と商用動画検索で成長します〜"
                        ]
                    elif score >= 5:
                        feedback_responses = [
                            "まぁまぁですね〜 もっと良い応答と商用動画検索ができるよう頑張ります♪",
                            "ふむふむ〜 まだまだ学習が必要ですね〜 プリキュア見て商用コンテンツも勉強します♪",
                            "普通かぁ〜 次はもっと素敵な応答と商用動画検索しますからね〜♪"
                        ]
                    else:
                        feedback_responses = [
                            "うーん、まだまだですね〜 もっと勉強して良い応答と商用動画検索できるようになります♪",
                            "ごめんなさい〜 次はもっと頑張って素敵な商用コンテンツも見つけますね〜♪",
                            "えーん、もっと学習してプリキュアパワーと商用検索で素敵な応答できるようになりますから〜♪"
                        ]
                    
                    print(f"\n{self.name}: {random.choice(feedback_responses)}")
                    continue
                
                # メイン応答生成
                ai_response = self.generate_response(user_input)
                print(f"\n{self.name}: {ai_response}")
                
                conversation_count += 1
                
                # 定期的なフィードバック要求とプリキュア豆知識
                if conversation_count % 5 == 0:
                    print(f"\n{self.name}: この応答はいかがでしたか？1-10で評価していただけると学習に役立ちます♪")
                elif conversation_count % 3 == 0 and random.random() < 0.6:
                    # 時間帯に応じた豆知識（商用コンテンツ統合版）
                    time_period = self.get_time_period()
                    if time_period == 'morning':
                        precure_facts = [
                            f"朝のプリキュア豆知識〜！{random.choice(self.favorite_precures)}は朝が得意そうですよね〜♪ 商用動画でも朝活コンテンツ人気です〜",
                            "朝の変身シーンって特にキラキラして見えますよね〜♪ 商用利用可能な朝の動画も素敵ですよ〜",
                            f"朝は創作活動に最適な時間です〜♪ 商用利用できるアート動画で一緒にお絵描きしませんか〜？"
                        ]
                    elif time_period == 'afternoon':
                        precure_facts = [
                            f"お昼のプリキュア豆知識〜！{random.choice(self.favorite_precures)}とお昼ごはん食べたいな〜♪ 商用動画でお料理コンテンツも探せます〜",
                            "お昼休みにプリキュアの変身ポーズの練習、いかがですか〜？商用利用可能なダンス動画もありますよ〜",
                            f"午後の光で撮影された商用動画は特に綺麗に見えますね〜♪ プリキュア関連も探してみませんか〜？"
                        ]
                    else:  # evening
                        precure_facts = [
                            f"夜のプリキュア豆知識〜！{random.choice(self.favorite_precures)}と一緒に星空を見たいな〜♪ 商用の癒し動画もおすすめです〜",
                            "夜の変身シーンって幻想的で素敵ですよね〜♪ 商用利用可能な夜景動画も美しいですよ〜",
                            f"夜はゆっくりと商用利用できる教育動画を見る時間〜♪ プリキュアで学ぶ動画もあるかも〜？"
                        ]
                    
                    print(f"{self.name}: {random.choice(precure_facts)}")
                
                # 学習進捗表示（商用コンテンツ統合版）
                if conversation_count % 10 == 0:
                    learning_messages = [
                        f"🧠 学習レポート: {conversation_count}回の会話から学習中です〜♪ 商用動画検索も{len(self.commercial_content)}個成功〜",
                        f"📈 成長中〜！{conversation_count}回のお話といろいろ覚えました〜 商用コンテンツも得意になってます〜",
                        f"🌟 学習パワー充電中〜！{conversation_count}回分のデータとYouTube検索で賢くなってます〜♪"
                    ]
                    print(f"\n{self.name}: {random.choice(learning_messages)}")
                
            except KeyboardInterrupt:
                print(f"\n\n{self.name}: わぁ〜ん！急に止まっちゃった〜")
                print(f"{self.name}: でも学習データと商用動画情報はちゃんと保存してありますからね〜♪")
                print(f"{self.name}: また今度お話しして動画検索もしましょう〜♪")
                break
            except Exception as e:
                error_messages = [
                    "あわわ〜！なんかエラーが起こっちゃいました〜 でも商用動画検索は大丈夫です〜",
                    "きゃー！システムがちょっと困ってます〜 プリキュアパワーで復旧します〜",
                    "えーん！何か変なことになっちゃった〜 でも商用コンテンツ機能は生きてます〜"
                ]
                print(f"\n{self.name}: {random.choice(error_messages)}")
                print(f"{self.name}: エラー内容: {str(e)}")
                print(f"{self.name}: でも大丈夫！続けてお話しできますよ〜♪")

    def get_learning_stats(self) -> Dict:
        """学習統計取得（商用コンテンツ統合版）"""
        try:
            conn = sqlite3.connect(self.knowledge_base.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM precure_conversations')
            total_conversations = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(quality_score) FROM precure_conversations WHERE quality_score > 0')
            avg_score = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT personality_mode, COUNT(*) FROM precure_conversations GROUP BY personality_mode')
            mode_stats = dict(cursor.fetchall())
            
            cursor.execute('SELECT topic, COUNT(*) FROM precure_conversations GROUP BY topic')
            topic_stats = dict(cursor.fetchall())
            
            cursor.execute('SELECT COUNT(*) FROM commercial_content')
            total_commercial_videos = cursor.fetchone()[0]
            
            cursor.execute('SELECT search_query, COUNT(*) FROM commercial_content GROUP BY search_query')
            search_stats = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_conversations': total_conversations,
                'average_score': round(avg_score, 2),
                'mode_distribution': mode_stats,
                'topic_distribution': topic_stats,
                'total_commercial_videos': total_commercial_videos,
                'search_statistics': search_stats
            }
        except Exception:
            return {
                'total_conversations': len(self.conversation_history),
                'average_score': 0.0,
                'mode_distribution': {},
                'topic_distribution': {},
                'total_commercial_videos': len(self.commercial_content),
                'search_statistics': {}
            }

    def show_learning_dashboard(self):
        """学習ダッシュボード表示（商用コンテンツ統合版）"""
        stats = self.get_learning_stats()
        
        print("\n" + "=" * 60)
        print("🧠 キュアAI Commercial 学習ダッシュボード 🧠")
        print("=" * 60)
        print(f"📊 総会話数: {stats['total_conversations']}回")
        print(f"⭐ 平均評価: {stats['average_score']}/10.0")
        print(f"📹 発見した商用動画: {stats['total_commercial_videos']}個")
        print(f"🕒 現在時刻: {datetime.now().strftime('%H:%M')}")
        print(f"🌅 時間帯: {self.get_time_period()}")
        
        if stats['mode_distribution']:
            print(f"\n🎭 個性モード使用統計:")
            mode_names = {'cute': '可愛い', 'tsundere': 'ツンデレ', 'sweet': '甘えん坊'}
            for mode, count in stats['mode_distribution'].items():
                mode_name = mode_names.get(mode, mode)
                print(f"   {mode_name}: {count}回")
        
        if stats['topic_distribution']:
            print(f"\n📚 話題統計:")
            for topic, count in stats['topic_distribution'].items():
                print(f"   {topic}: {count}回")
        
        if stats['search_statistics']:
            print(f"\n🔍 検索クエリ統計:")
            for query, count in stats['search_statistics'].items():
                if query:  # 空でないクエリのみ表示
                    print(f"   「{query}」: {count}回")
        
        print("=" * 60)
        print("💖 プリキュアAI × 商用コンテンツ検索の統合システム")
        print("🌟 Creative Commons動画のみを安全に提供")
        print("=" * 60)

def main():
    """メインエントリーポイント"""
    current_time = datetime.now()
    time_period = 'morning' if 5 <= current_time.hour < 12 else ('afternoon' if 12 <= current_time.hour < 18 else 'evening')
    time_emojis = {'morning': '🌅', 'afternoon': '🌞', 'evening': '🌙'}
    
    print("🌟 Precure × Commercial Content AI System Starting... 🌟")
    print(f"{time_emojis[time_period]} 時間帯別挨拶システム Loading... ✅")
    print("🧠 Advanced Learning Module Loading... ✅")
    print("💖 Precure Database Initializing... ✅") 
    print("🎨 Art & Creativity Engine Ready... ✅")
    print("🎭 Multi-Personality System Online... ✅")
    print("📹 YouTube Commercial Content Extractor Loading... ", end="")
    
    # YouTube API キー設定チェック
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    if youtube_api_key:
        print("✅")
        print("🔍 Commercial Video Search Ready... ✅")
    else:
        print("⚠️")
        print("⚠️  YouTube API Key Not Found - Video search disabled")
        print("💡 Set YOUTUBE_API_KEY environment variable to enable video search")
    
    print(f"🕒 Current Time: {current_time.strftime('%H:%M')} ({time_period}) ✅")
    
    time.sleep(2)
    
    try:
        print("\n✨ === キュアAI Commercial 起動完了 === ✨")
        print("💫 プリキュアと商用コンテンツ検索が融合した次世代AI！")
        print("🕒 時間帯対応挨拶 + 📹 Creative Commons動画自動検索")
        print("🎭 3つの個性 × 🔍 ビジネス利用可能コンテンツ発見")
        
        ai = PrecureCommercialAI(youtube_api_key)
        
        # 学習統計表示オプション
        if len(sys.argv) > 1 and sys.argv[1] == '--stats':
            ai.show_learning_dashboard()
            return
        
        ai.chat()
        
    except Exception as e:
        print(f"🚨 システム初期化エラー: {e}")
        print("申し訳ございません。システム管理者にお問い合わせください。")
    finally:
        print("\n🌟 キュアAI Commercial - お疲れ様でした！🌟")
        print("💖 プリキュア愛と商用コンテンツでまたお会いしましょう！")

# 使用例とテスト関数
def test_integrated_system():
    """統合システムテスト"""
    print("🧪 プリキュア×商用コンテンツAI統合テスト")
    print("=" * 50)
    
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not youtube_api_key:
        print("⚠️  YouTube API キーが必要です")
        print("環境変数 YOUTUBE_API_KEY を設定してテストを実行してください")
        return
    
    ai = PrecureCommercialAI(youtube_api_key)
    
    # テストクエリ
    test_queries = [
        "プリキュア 検索して",
        "アニメの動画探して",
        "音楽 商用利用",
        "教育コンテンツ見つけて",
        "アート チュートリアル"
    ]
    
    print("📝 テストクエリで応答をテスト中...")
    for query in test_queries:
        print(f"\n👤 テスト入力: {query}")
        response = ai.generate_response(query)
        print(f"🤖 AI応答: {response[:100]}...")  # 最初の100文字のみ表示
        time.sleep(1)  # API制限対策
    
    print(f"\n📊 テスト結果: {len(ai.commercial_content)}個の商用動画を発見")
    print("✅ 統合システムテスト完了")

def demo_personality_modes():
    """個性モードデモ"""
    print("🎭 個性モードデモンストレーション")
    print("=" * 40)
    
    ai = PrecureCommercialAI()
    test_input = "プリキュアが大好きです"
    
    # 各モードでの応答をテスト
    for mode in ['cute', 'tsundere', 'sweet']:
        context = ai.create_context(test_input)
        context.personality_mode = mode
        response = ai.generate_precure_response(test_input, context)
        
        mode_names = {'cute': '可愛い', 'tsundere': 'ツンデレ', 'sweet': '甘えん坊'}
        print(f"\n{mode_names[mode]}モード:")
        print(f"🤖 {response}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_integrated_system()
        elif sys.argv[1] == "demo":
            demo_personality_modes()
        elif sys.argv[1] == "--stats":
            main()
        else:
            print("使用法:")
            print("  python script.py          # 通常実行")
            print("  python script.py test     # 統合テスト")
            print("  python script.py demo     # 個性モードデモ")
            print("  python script.py --stats  # 統計表示")
    else:
        main()
