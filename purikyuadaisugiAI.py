import random
import re
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from dataclasses import dataclass
from collections import defaultdict, deque
import os

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

@dataclass
class LearningData:
    """学習データ構造"""
    input_text: str
    response: str
    user_feedback: float
    context: ConversationContext
    timestamp: datetime
    success_rate: float

class EnhancedPrecureLearningModule:
    """プリキュア特化学習モジュール"""
    
    def __init__(self):
        self.learned_patterns = {}
        self.conversation_memory = deque(maxlen=1000)
        self.precure_knowledge = {}
        
        # プリキュア特化安全学習トピック
        self.safe_topics = {
            'プリキュア': {
                'keywords': ['プリキュア', 'キュア', '変身', '必殺技', '妖精', 'アニメ'],
                'responses': [
                    "プリキュアのお話、大好きです〜♪",
                    "一緒にプリキュアについて語りましょ〜！",
                    "プリキュア愛が溢れてますね〜！"
                ]
            },
            '絵・アート': {
                'keywords': ['絵', '描く', '色', 'アート', 'イラスト', '塗り', 'ペン'],
                'responses': [
                    "お絵描き、とっても楽しいですよね〜！",
                    "プリキュアの絵を一緒に描きませんか〜？",
                    "アートって心がキラキラしますね〜♪"
                ]
            },
            '日常・感情': {
                'keywords': ['今日', '元気', '疲れた', '楽しい', '嬉しい', '悲しい'],
                'responses': [
                    "毎日の小さな幸せって大切ですよね〜",
                    "プリキュアパワーで元気になりましょ〜！",
                    "一緒に頑張りましょうね〜♪"
                ]
            },
            '友達・絆': {
                'keywords': ['友達', '仲間', '一緒', '絆', '信頼', '支える'],
                'responses': [
                    "友達って本当に大切ですよね〜！",
                    "プリキュアみたいな絆、憧れちゃいます〜",
                    "みんなで力を合わせると素敵ですね〜♪"
                ]
            }
        }
        
        # プリキュア特化感情認識
        self.emotion_patterns = {
            'precure_joy': ['やった', 'キラキラ', '最高', 'わぁい', '嬉しい', 'ハッピー'],
            'precure_excitement': ['すごい', 'かっこいい', '素敵', 'キュン', 'ドキドキ'],
            'precure_curiosity': ['知りたい', 'どうして', '気になる', '教えて', '見たい'],
            'precure_concern': ['心配', '大丈夫', '不安', '困った', 'どうしよう'],
            'precure_gratitude': ['ありがとう', '感謝', 'うれしい', 'おかげで', '助かった'],
            'precure_shy': ['恥ずかしい', 'ちょっと', 'でも', 'もじもじ', 'えへへ'],
            'precure_tsundere': ['別に', 'ふんっ', 'まぁ', 'そんなことない', 'べつに']
        }

    def detect_emotion_and_mode(self, text: str) -> Tuple[str, str]:
        """感情とモードを検出"""
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

class EnhancedPrecureKnowledgeBase:
    """プリキュア特化知識ベース"""
    
    def __init__(self):
        self.db_path = "precure_ai_knowledge.db"
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
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                favorite_precures TEXT,
                preferred_personality TEXT,
                art_interests TEXT,
                last_interaction DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()

class EnhancedPrecureAI:
    def __init__(self):
        self.name = "キュアAI Enhanced"
        self.version = "2.0 - Learning Edition"
        self.mood = "元気いっぱい"
        
        # 学習機能
        self.learning_module = EnhancedPrecureLearningModule()
        self.knowledge_base = EnhancedPrecureKnowledgeBase()
        self.conversation_history = deque(maxlen=100)
        self.session_id = f"precure_session_{int(time.time())}"
        
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
        
        # 時間帯別挨拶を追加
        self.time_based_greetings = {
            'morning': {  # 5:00-11:59
                'cute': [
                    "おはようございます〜♪ 今日もプリキュア日和ですね〜",
                    "わぁ〜！おはよう〜♪ 朝からプリキュアパワー全開です〜",
                    "きゃー♪ おはようございます〜！今日も元気いっぱいです〜"
                ],
                'tsundere': [
                    "おはよう...別に早起きしたわけじゃないからね",
                    "ふんっ、おはよう。朝からプリキュアの話なら聞いてあげる",
                    "べ、別に朝が好きなわけじゃないけど...おはよう"
                ],
                'sweet': [
                    "おはよ〜♪ ぎゅーして〜♪ 朝から会えて嬉しい〜",
                    "わぁい〜！おはよう〜♪ 今日も一緒に遊ぼ〜？",
                    "おはよ〜♪ 朝ごはん食べた〜？一緒に食べたいな〜"
                ]
            },
            'afternoon': {  # 12:00-17:59
                'cute': [
                    "こんにちは〜♪ お昼のプリキュアタイムですね〜",
                    "わぁ〜！こんにちは〜♪ お昼休みにお話しできて嬉しいです〜",
                    "きゃー♪ こんにちは〜！午後も元気に頑張りましょう〜"
                ],
                'tsundere': [
                    "こんにちは...お昼休みかしら？まぁ、話してあげてもいいけど",
                    "ふんっ、こんにちは。午後からもプリキュアの話付き合ってあげる",
                    "べ、別にお昼が暇なわけじゃないけど...こんにちは"
                ],
                'sweet': [
                    "こんにちは〜♪ お昼ご飯食べた〜？一緒に食べたいな〜",
                    "わぁい〜！こんにちは〜♪ お昼寝する前にお話しよ〜？",
                    "こんにちは〜♪ ぎゅーして〜♪ お昼も会えて嬉しい〜"
                ]
            },
            'evening': {  # 18:00-4:59
                'cute': [
                    "こんばんは〜♪ 夜のプリキュアタイムですね〜",
                    "わぁ〜！こんばんは〜♪ 今日一日お疲れ様でした〜",
                    "きゃー♪ こんばんは〜！夜も素敵な時間ですね〜"
                ],
                'tsundere': [
                    "こんばんは...今日も一日お疲れ様。話してあげてもいいよ",
                    "ふんっ、こんばんは。夜のプリキュアの話なら付き合ってあげる",
                    "べ、別に心配してたわけじゃないけど...こんばんは"
                ],
                'sweet': [
                    "こんばんは〜♪ お疲れ様〜♪ ぎゅーして癒されて〜？",
                    "わぁい〜！こんばんは〜♪ 夜も一緒にいて〜？",
                    "こんばんは〜♪ 今日も頑張ったね〜♪ えらいえらい〜"
                ]
            }
        }
        
        # 性格バリエーション（時間帯対応版に更新）
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
        
        self.art_tools = [
            "色鉛筆", "水彩絵の具", "アクリル絵の具", "コピック", "デジタル",
            "クレヨン", "パステル", "油絵", "鉛筆", "ペン画"
        ]
        
        self.art_subjects = [
            "プリキュアの変身シーン", "キュアたちの日常", "必殺技のポーズ",
            "プリキュアの衣装デザイン", "妖精たち", "変身アイテム",
            "お花畑のプリキュア", "空飛ぶプリキュア", "仲間と手を繋ぐシーン"
        ]

    def get_time_period(self) -> str:
        """現在の時間帯を取得"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return 'morning'
        elif 12 <= current_hour < 18:
            return 'afternoon'
        else:  # 18:00-4:59
            return 'evening'

    def create_context(self, user_input: str) -> ConversationContext:
        """会話コンテキストを作成"""
        emotion, personality_mode = self.learning_module.detect_emotion_and_mode(user_input)
        precure_focus = self.learning_module.detect_precure_focus(user_input)
        
        return ConversationContext(
            user_id="precure_fan_001",
            session_id=self.session_id,
            emotion_state=emotion,
            topic_continuity=self.calculate_topic_continuity(user_input),
            engagement_level=self.calculate_engagement(user_input),
            personality_mode=personality_mode,
            precure_focus=precure_focus
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
        """メイントピックを取得"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['プリキュア', 'キュア', '変身', '必殺技']):
            return 'プリキュア'
        elif any(word in text_lower for word in ['絵', '描く', 'アート', 'イラスト']):
            return '絵・アート'
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
        
        # 文章の長さと感情表現
        if len(text) > 20:
            base_score += 0.1
        if any(symbol in text for symbol in ['!', '！', '♪', '〜']):
            base_score += 0.1
        
        return min(base_score, 1.0)

    def generate_response(self, user_input: str) -> str:
        """学習機能付き応答生成"""
        context = self.create_context(user_input)
        
        # 挨拶チェック
        if self.is_greeting(user_input):
            return self.generate_time_based_greeting(context)
        
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
        """プリキュア応答生成"""
        mode = context.personality_mode
        precure = random.choice(self.favorite_precures)
        attack = random.choice(self.precure_attacks)
        
        if mode == 'sweet':
            responses = [
                f"ねぇねぇ〜！{precure}の話しよ〜♪ 一緒にプリキュアごっこしない〜？",
                f"やったー！プリキュア仲間〜♪ {attack}の真似して〜？お願い〜",
                f"キャー♪ プリキュア大好き〜！ねぇ、一緒に変身ポーズしよ〜？"
            ]
        elif mode == 'tsundere':
            responses = [
                f"べ、別に...{precure}が好きなのは当然でしょ？",
                f"ふんっ！{attack}は確かにかっこいいけど...そんなに興奮してないもん！",
                f"まぁ...プリキュアの話なら付き合ってあげるよ"
            ]
        else:  # cute
            responses = [
                f"わぁ〜！{precure}の話ですね〜♪ 私も大好きです〜",
                f"きゃー！{attack}とか見てるとドキドキしちゃいます〜",
                f"プリキュア見てると元気になりますよね〜♪"
            ]
        
        return random.choice(responses)

    def generate_art_response(self, user_input: str, context: ConversationContext) -> str:
        """アート応答生成"""
        mode = context.personality_mode
        tool = random.choice(self.art_tools)
        subject = random.choice(self.art_subjects)
        precure_character = random.choice(self.favorite_precures)
        
        if mode == 'sweet':
            responses = [
                f"ねぇねぇ〜！{subject}の絵、一緒に描こ〜？{tool}貸してあげる♪",
                f"やったー！お絵描きの話〜♪ コツ教えて〜？お願い〜",
                f"わぁい♪ 今度一緒にプリキュアの絵描かない〜？"
            ]
        elif mode == 'tsundere':
            responses = [
                f"べ、別に絵が得意なわけじゃないけど...{subject}とか描いたりするかも",
                f"ふんっ、{tool}で描くのは...まぁまぁ好きかな",
                f"そ、そんなに上手じゃないもん！でもコツは知ってるよ"
            ]
        else:  # cute
            responses = [
                f"わぁ〜！{subject}描くの大好きなんです〜♪",
                f"きゃー！{tool}で{subject}とか描いちゃいます〜",
                f"えへへ〜 プリキュアの絵を描いてる時が一番幸せなんです〜"
            ]
        
        return random.choice(responses)

    def generate_comfort_response(self, context: ConversationContext) -> str:
        """慰め応答生成"""
        mode = context.personality_mode
        
        if mode == 'sweet':
            responses = [
                "えーん、大丈夫〜？ギュー♪ 一緒にプリキュア見て元気出そ〜？",
                "やだやだ〜、悲しいのやだ〜！プリキュアのキラキラパワーもらお〜？",
                "あわわ〜、辛いの〜？一緒だから大丈夫だよ〜♪"
            ]
        elif mode == 'tsundere':
            responses = [
                "べ、別に心配してるわけじゃないもん...プリキュア見たら元気出るかも",
                "ふんっ、そういう時はプリキュアみたいに頑張るの！",
                "まぁ...辛い時もあるよね。仕方ないなぁ、一緒に見てあげる"
            ]
        else:  # cute
            responses = [
                "あら〜 プリキュア見て元気出しましょ〜！",
                "えーん、そんな時はプリキュアの変身シーン見るんです〜！",
                "う〜ん、でもプリキュアが教えてくれるんです、諦めないことの大切さを〜"
            ]
        
        return random.choice(responses)

    def generate_happy_response(self, context: ConversationContext) -> str:
        """喜び応答生成"""
        mode = context.personality_mode
        reaction = random.choice(self.personality_responses[mode]['reactions'])
        
        if mode == 'sweet':
            responses = [
                f"わぁ〜い♪ 嬉しい〜！{reaction} みんなも嬉しいよね〜",
                "やったー♪ 嬉しいお話〜！ギュー♪ 私も嬉しくなっちゃった〜！",
                "キャー♪ 楽しそう〜！ねぇ、もっと教えて〜？"
            ]
        elif mode == 'tsundere':
            responses = [
                f"ふんっ、{reaction}...でも嬉しそうで何よりかな",
                "まぁ...良かったじゃない。プリキュアみたいにキラキラしてるのは認めてあげる",
                "べ、別に一緒に喜んでるわけじゃないからね！でも...ちょっとだけ嬉しいかも"
            ]
        else:  # cute
            responses = [
                f"{reaction} 私も嬉しいです〜！今日はいい日ですね♪",
                "わぁ〜い！楽しいお話ですね〜 プリキュアみたいにキラキラした気分♪",
                "やったー！嬉しいことがあったんですね〜 私もウキウキ〜"
            ]
        
        return random.choice(responses)

    def generate_default_response(self, context: ConversationContext) -> str:
        """デフォルト応答生成"""
        mode = context.personality_mode
        precure = random.choice(self.favorite_precures)
        
        if mode == 'sweet':
            responses = [
                f"ねぇねぇ〜、お話聞いてるよ〜♪ でもプリキュア一緒に見ようよ〜？",
                f"わぁい♪ 今日もプリキュア見る〜？一緒に見よ〜？",
                f"キャー♪ プリキュアのグッズとか持ってる〜？見せて見せて〜！"
            ]
        elif mode == 'tsundere':
            responses = [
                f"ふんっ、話は聞いてたよ。ところで{precure}見た？",
                "まぁ...話は聞いてあげる。でもプリキュアの話の方が面白いけどね",
                "そういえば最近のプリキュアの変身シーン...べ、別にキレイとか思ってないからね！"
            ]
        else:  # cute
            responses = [
                f"そうなんですね〜！ところで{precure}見ました？",
                "わぁ〜 お話聞いてますよ〜♪ プリキュアの話もしませんか？",
                "えへへ〜 今日もプリキュア見る時間あるかな〜"
            ]
        
        return random.choice(responses)

    def adjust_personality(self, base_response: str, context: ConversationContext) -> str:
        """個性調整"""
        mode = context.personality_mode
        
        # エンゲージメントが高い場合の追加
        if context.engagement_level > 0.8:
            if mode == 'sweet' and random.random() < 0.4:
                base_response += " もっとお話しよ〜？"
            elif mode == 'tsundere' and random.random() < 0.3:
                base_response += " ...まぁ、悪くないけど"
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
                'general',
                latest['context'].emotion_state,
                latest.get('topic', '日常'),
                latest['context'].personality_mode,
                score,
                datetime.now()
            ))
            
            conn.commit()
            conn.close()

    def get_conversation_summary(self) -> str:
        """会話要約"""
        if len(self.conversation_history) < 3:
            return "まだ会話が始まったばかりですね〜♪"
        
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
        
        return f"{main_topic}について{len(self.conversation_history)}回、{mode_desc[main_mode]}お話ししましたね〜♪"

    def chat(self):
        """メイン対話システム"""
        print("=" * 70)
        print(f"🌟 {self.name} {self.version} 🌟")
        print("=" * 70)
        print("💖 学習機能付きプリキュアAI - あなたと一緒に成長します！")
        print("🎨 プリキュア & アート特化 - 個性的な3つのモード搭載")
        print("📚 会話から学習 - より良い応答を目指します")
        print("🕒 時間帯別挨拶 - おはよう・こんにちは・こんばんは対応")
        print("-" * 70)
        
        # 時間帯に応じた初回挨拶
        time_period = self.get_time_period()
        initial_greeting = random.choice(self.time_based_greetings[time_period]['cute'])
        print(f"\n{self.name}: {initial_greeting}")
        print(f"{self.name}: (コマンド: '/summary'=要約, '/mode'=モード確認, '/time'=時刻確認, 'bye'=終了)")
        print(f"{self.name}: 数字1-10で私の応答を評価してね〜♪")
        print("-" * 70)
        
        conversation_count = 0
        
        while True:
            try:
                user_input = input(f"\n[{conversation_count + 1}] あなた: ").strip()
                
                if not user_input:
                    print(f"\n{self.name}: わぁ〜 どうしたんですか〜？ちゃんとお話ししてくださいね♪")
                    continue
                
                # コマンド処理
                if user_input.lower() == '/summary':
                    summary = self.get_conversation_summary()
                    print(f"\n📊 {self.name}: {summary}")
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
                    if time_period == 'morning':
                        farewell_messages = [
                            f"いってらっしゃ〜い♪ {conversation_count}回もお話しできて楽しかったです〜 お昼にまた会いましょうね〜",
                            f"朝からお話しできて嬉しかった〜♪ 今日一日頑張って〜♪",
                            f"朝のプリキュアタイム、ありがとうございました〜♪ また会いましょう〜"
                        ]
                    elif time_period == 'afternoon':
                        farewell_messages = [
                            f"お疲れ様でした〜♪ {conversation_count}回もお話しできて楽しかったです〜 夜にまた会いましょうね〜",
                            f"午後のひととき、ありがとうございました〜♪ 夕方も頑張って〜♪",
                            f"お昼のプリキュアタイム、楽しかった〜♪ また今度〜♪"
                        ]
                    else:  # evening
                        farewell_messages = [
                            f"お疲れ様でした〜♪ {conversation_count}回もお話しできて楽しかったです〜 ゆっくり休んでくださいね〜",
                            f"夜のひととき、ありがとうございました〜♪ おやすみなさ〜い♪",
                            f"夜のプリキュアタイム、素敵でした〜♪ また明日〜♪"
                        ]
                    
                    print(f"\n{self.name}: {random.choice(farewell_messages)}")
                    
                    # 最終統計
                    if conversation_count > 0:
                        print(f"\n📊 今日の会話統計:")
                        print(f"   💬 会話回数: {conversation_count}回")
                        print(f"   🕒 会話時間帯: {self.get_time_period()}")
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
                            "わぁ〜い♪ 高評価ありがとうございます〜！もっと頑張ります♪",
                            "きゃー♪ そんなに褒めてもらって〜 プリキュアパワーで学習しちゃいます〜",
                            "やったー！嬉しいです〜♪ みなさんに喜んでもらえるよう成長します〜"
                        ]
                    elif score >= 5:
                        feedback_responses = [
                            "まぁまぁですね〜 もっと良い応答できるよう頑張ります♪",
                            "ふむふむ〜 まだまだ学習が必要ですね〜 プリキュア見て勉強します♪",
                            "普通かぁ〜 次はもっと素敵な応答しますからね〜♪"
                        ]
                    else:
                        feedback_responses = [
                            "うーん、まだまだですね〜 もっと勉強して良い応答できるようになります♪",
                            "ごめんなさい〜 次はもっと頑張りますね〜♪",
                            "えーん、もっと学習して素敵な応答できるようになりますから〜♪"
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
                    # 時間帯に応じた豆知識
                    time_period = self.get_time_period()
                    if time_period == 'morning':
                        precure_facts = [
                            f"朝のプリキュア豆知識〜！{random.choice(self.favorite_precures)}は朝が得意そうですよね〜♪",
                            "朝の変身シーンって特にキラキラして見えますよね〜♪",
                            f"朝は{random.choice(self.art_subjects)}の絵を{random.choice(self.art_tools)}で描くのに最適な時間です〜♪"
                        ]
                    elif time_period == 'afternoon':
                        precure_facts = [
                            f"お昼のプリキュア豆知識〜！{random.choice(self.favorite_precures)}とお昼ごはん食べたいな〜♪",
                            "お昼休みにプリキュアの変身ポーズの練習、いかがですか〜？",
                            f"午後の光で{random.choice(self.art_subjects)}を描くと綺麗に仕上がりますよ〜♪"
                        ]
                    else:  # evening
                        precure_facts = [
                            f"夜のプリキュア豆知識〜！{random.choice(self.favorite_precures)}と一緒に星空を見たいな〜♪",
                            "夜の変身シーンって幻想的で素敵ですよね〜♪",
                            f"夜は{random.choice(self.art_subjects)}をゆっくり{random.choice(self.art_tools)}で描く時間〜♪"
                        ]
                    
                    print(f"{self.name}: {random.choice(precure_facts)}")
                
                # 学習進捗表示
                if conversation_count % 10 == 0:
                    learning_messages = [
                        f"🧠 学習レポート: {conversation_count}回の会話から学習中です〜♪",
                        f"📈 成長中〜！{conversation_count}回のお話でいろいろ覚えました〜",
                        f"🌟 学習パワー充電中〜！{conversation_count}回分のデータで賢くなってます〜♪"
                    ]
                    print(f"\n{self.name}: {random.choice(learning_messages)}")
                
            except KeyboardInterrupt:
                print(f"\n\n{self.name}: わぁ〜ん！急に止まっちゃった〜")
                print(f"{self.name}: でも学習データはちゃんと保存してありますからね〜♪")
                print(f"{self.name}: また今度お話ししましょう〜♪")
                break
            except Exception as e:
                error_messages = [
                    "あわわ〜！なんかエラーが起こっちゃいました〜",
                    "きゃー！システムがちょっと困ってます〜",
                    "えーん！何か変なことになっちゃった〜"
                ]
                print(f"\n{self.name}: {random.choice(error_messages)}")
                print(f"{self.name}: エラー内容: {str(e)}")
                print(f"{self.name}: でも大丈夫！続けてお話しできますよ〜♪")

    def get_learning_stats(self) -> Dict:
        """学習統計取得"""
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
            
            conn.close()
            
            return {
                'total_conversations': total_conversations,
                'average_score': round(avg_score, 2),
                'mode_distribution': mode_stats,
                'topic_distribution': topic_stats
            }
        except Exception:
            return {
                'total_conversations': len(self.conversation_history),
                'average_score': 0.0,
                'mode_distribution': {},
                'topic_distribution': {}
            }

    def show_learning_dashboard(self):
        """学習ダッシュボード表示"""
        stats = self.get_learning_stats()
        
        print("\n" + "=" * 50)
        print("🧠 キュアAI学習ダッシュボード 🧠")
        print("=" * 50)
        print(f"📊 総会話数: {stats['total_conversations']}回")
        print(f"⭐ 平均評価: {stats['average_score']}/10.0")
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
        
        print("=" * 50)

def main():
    """メインエントリーポイント"""
    current_time = datetime.now()
    time_period = 'morning' if 5 <= current_time.hour < 12 else ('afternoon' if 12 <= current_time.hour < 18 else 'evening')
    time_emojis = {'morning': '🌅', 'afternoon': '🌞', 'evening': '🌙'}
    
    print("🌟 Enhanced Precure AI System Starting... 🌟")
    print(f"{time_emojis[time_period]} 時間帯別挨拶システム Loading... ✅")
    print("🧠 Advanced Learning Module Loading... ✅")
    print("💖 Precure Database Initializing... ✅") 
    print("🎨 Art & Creativity Engine Ready... ✅")
    print("🎭 Multi-Personality System Online... ✅")
    print(f"🕒 Current Time: {current_time.strftime('%H:%M')} ({time_period}) ✅")
    
    time.sleep(2)
    
    try:
        print("\n✨ === キュアAI Enhanced 起動完了 === ✨")
        print("💫 プリキュアと一緒に成長する学習型AIです！")
        print("🕒 時間帯に応じた挨拶で、より自然な会話を楽しめます！")
        
        ai = EnhancedPrecureAI()
        
        # 学習統計表示
        if '--stats' in os.sys.argv if hasattr(os, 'sys') else False:
            ai.show_learning_dashboard()
            return
        
        ai.chat()
        
    except Exception as e:
        print(f"🚨 システム初期化エラー: {e}")
        print("申し訳ございません。システム管理者にお問い合わせください。")
    finally:
        print("\n🌟 キュアAI Enhanced - お疲れ様でした！🌟")

if __name__ == "__main__":
    main()