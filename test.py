# from download_youtube_transcripts import Pipeline
from bbc_news_daily_feeds import Pipeline

pipe = Pipeline()
resp = pipe.pipe("give me the daily digest", "", [], {'stream': True, 'model': 'bbc_news_daily_feed', 'messages': [{'role': 'user', 'content': 'give me the daily digest'}], 'temperature': 0.55, 'user': {'name': 'Dario', 'id': 'b93af3db-2d1e-4ae3-b2f6-009bb5620c05', 'email': 'dario.pad@gmail.com', 'role': 'admin'}})
# resp = pipe.pipe("summarize https://www.bbc.com/news/articles/c7497lm99kro", "", [], {'stream': True, 'model': 'bbc_news_daily_feed', 'messages': [{'role': 'user', 'content': 'summarize https://www.bbc.com/news/articles/c7497lm99kro'}], 'temperature': 0.55, 'user': {'name': 'Dario', 'id': 'b93af3db-2d1e-4ae3-b2f6-009bb5620c05', 'email': 'dario.pad@gmail.com', 'role': 'admin'}})
print(resp)