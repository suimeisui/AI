import requests
import json
import os
from datetime import datetime
import re
from urllib.parse import parse_qs, urlparse

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
                    video_info = {
                        'video_id': item['id']['videoId'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'][:200] + '...',
                        'channel': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'thumbnail': item['snippet']['thumbnails']['default']['url'],
                        'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                    }
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
    
    def get_channel_commercial_videos(self, channel_id, max_results=20):
        """チャンネルの商用利用可能動画を取得"""
        search_url = f"{self.base_url}/search"
        
        params = {
            'part': 'snippet',
            'channelId': channel_id,
            'type': 'video',
            'videoLicense': 'creativeCommon',
            'videoEmbeddable': 'true',
            'maxResults': max_results,
            'key': self.api_key,
            'order': 'date'
        }
        
        try:
            response = requests.get(search_url, params=params)
            if response.status_code == 200:
                data = response.json()
                return [item['id']['videoId'] for item in data.get('items', [])]
            return []
            
        except Exception as e:
            print(f"チャンネル検索エラー: {e}")
            return []

class CommercialUseAIChat:
    """商用利用可能コンテンツ専用AI会話クラス"""
    
    def __init__(self, youtube_api_key, openai_api_key=None):
        self.youtube_extractor = YouTubeCommercialExtractor(youtube_api_key)
        self.openai_api_key = openai_api_key
        self.conversation_history = []
        self.commercial_content = []
        
    def search_and_add_content(self, query, max_results=10):
        """商用利用可能コンテンツを検索してコンテキストに追加"""
        print(f"商用利用可能なコンテンツを検索中: '{query}'")
        
        videos = self.youtube_extractor.search_commercial_videos(query, max_results)
        
        if videos:
            self.commercial_content.extend(videos)
            
            # コンテキスト作成
            context = f"以下は'{query}'に関する商用利用可能なYouTubeコンテンツです:\n\n"
            
            for i, video in enumerate(videos, 1):
                context += f"{i}. 【{video['title']}】\n"
                context += f"   チャンネル: {video['channel']}\n"
                context += f"   概要: {video['description']}\n"
                context += f"   URL: {video['url']}\n"
                context += f"   公開日: {video['published_at']}\n\n"
            
            self.conversation_history.append({
                "role": "system",
                "content": context
            })
            
            print(f"{len(videos)}件の商用利用可能コンテンツを見つけました。")
            return videos
        else:
            print("商用利用可能なコンテンツが見つかりませんでした。")
            return []
    
    def get_video_transcript_summary(self, video_id):
        """動画の要約情報を取得（詳細情報ベース）"""
        details = self.youtube_extractor.get_video_details(video_id)
        
        if details and details['commercial_use']:
            summary = {
                'title': details['title'],
                'channel': details['channel'],
                'description': details['description'][:500],  # 最初の500文字
                'duration': details['duration'],
                'views': details['view_count'],
                'commercial_use': True,
                'url': details['url']
            }
            return summary
        
        return None
    
    def chat_local(self, message):
        """ローカルAI（商用コンテンツベース応答）"""
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        message_lower = message.lower()
        
        # 検索キーワードの抽出
        search_keywords = ['検索', 'search', '探す', '見つけて', 'について']
        content_keywords = ['動画', 'video', 'コンテンツ', 'content']
        commercial_keywords = ['商用', 'commercial', 'ビジネス', 'business']
        
        if any(keyword in message_lower for keyword in search_keywords):
            # 検索クエリを抽出
            query = re.sub(r'(検索|search|探す|見つけて|について)', '', message_lower).strip()
            if query:
                videos = self.search_and_add_content(query)
                if videos:
                    response = f"'{query}'に関する商用利用可能なコンテンツを{len(videos)}件見つけました。\n"
                    response += "これらのコンテンツはすべて商用利用が可能です。どの動画について詳しく知りたいですか？"
                else:
                    response = f"申し訳ありませんが、'{query}'に関する商用利用可能なコンテンツは見つかりませんでした。"
            else:
                response = "何について検索したいですか？"
                
        elif any(keyword in message_lower for keyword in commercial_keywords):
            response = "商用利用可能なコンテンツのみを扱っています。Creative Commonsライセンスで埋め込み可能な動画のみを提供します。"
            
        elif any(keyword in message_lower for keyword in content_keywords):
            if self.commercial_content:
                response = f"現在、{len(self.commercial_content)}件の商用利用可能なコンテンツがあります。特定の動画について詳しく知りたい場合は、タイトルを教えてください。"
            else:
                response = "まずはキーワードで商用利用可能なコンテンツを検索してみましょう。"
                
        else:
            response = "商用利用可能なYouTubeコンテンツについてお手伝いします。検索したいキーワードを教えてください。"
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def chat_with_openai(self, message):
        """OpenAI APIを使用した高度な会話"""
        if not self.openai_api_key:
            return self.chat_local(message)
        
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # システムメッセージを追加
        system_message = {
            "role": "system",
            "content": "あなたは商用利用可能なYouTubeコンテンツの専門アシスタントです。Creative Commonsライセンスで埋め込み可能な動画のみを扱います。著作権に関して慎重に対応し、商用利用可能なコンテンツのみを推奨してください。"
        }
        
        messages = [system_message] + self.conversation_history[-10:]
        
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': messages,
                'max_tokens': 500,
                'temperature': 0.7
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                return ai_response
            else:
                return f"API エラー: {response.status_code}"
                
        except Exception as e:
            return f"通信エラー: {e}"
    
    def show_commercial_content(self):
        """商用利用可能コンテンツ一覧表示"""
        if not self.commercial_content:
            print("まだ商用利用可能なコンテンツがありません。")
            return
        
        print("\n=== 商用利用可能コンテンツ一覧 ===")
        for i, video in enumerate(self.commercial_content, 1):
            print(f"\n{i}. {video['title']}")
            print(f"   チャンネル: {video['channel']}")
            print(f"   URL: {video['url']}")
            print(f"   公開日: {video['published_at']}")

def main():
    """メイン実行関数"""
    print("YouTube 商用利用可能コンテンツ AI Chat")
    print("=" * 50)
    
    # API キー設定
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not youtube_api_key:
        print("YouTube API キーが設定されていません。")
        print("環境変数 YOUTUBE_API_KEY を設定してください。")
        return
    
    # AI チャット初期化
    ai_chat = CommercialUseAIChat(youtube_api_key, openai_api_key)
    
    print("商用利用可能なYouTubeコンテンツとの会話を開始します。")
    print("'quit'で終了、'list'でコンテンツ一覧表示")
    print("-" * 50)
    
    while True:
        user_input = input("\nあなた: ")
        
        if user_input.lower() in ['quit', 'exit', '終了']:
            print("アプリケーションを終了します。")
            break
        elif user_input.lower() == 'list':
            ai_chat.show_commercial_content()
            continue
            
        if user_input.strip():
            if openai_api_key:
                response = ai_chat.chat_with_openai(user_input)
            else:
                response = ai_chat.chat_local(user_input)
                
            print(f"\nAI: {response}")

# 使用例とテスト
def test_commercial_search():
    """商用利用可能コンテンツ検索テスト"""
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not youtube_api_key:
        print("YouTube API キーが必要です")
        return
    
    extractor = YouTubeCommercialExtractor(youtube_api_key)
    
    # テスト検索
    test_queries = ['music', 'education', 'tutorial']
    
    for query in test_queries:
        print(f"\n=== '{query}' の商用利用可能コンテンツ ===")
        videos = extractor.search_commercial_videos(query, 5)
        
        for video in videos:
            print(f"タイトル: {video['title']}")
            print(f"チャンネル: {video['channel']}")
            print(f"URL: {video['url']}")
            print("-" * 30)

if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "test":
        test_commercial_search()
    else:
        main()