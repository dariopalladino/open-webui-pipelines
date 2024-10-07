from download_youtube_transcripts import Pipeline

pipe = Pipeline()
resp = pipe.pipe('it extract wisdom https://www.youtube.com/watch?v=-IAwW3pUEew', "", [], {'stream': True, 'model': 'download_youtube_transcripts', 'messages': [{'role': 'user', 'content': 'extract wisdom from this url https://www.youtube.com/watch?v=5EfqHg49kMk'}], 'temperature': 0.55, 'user': {'name': 'Dario', 'id': 'b93af3db-2d1e-4ae3-b2f6-009bb5620c05', 'email': 'dario.pad@gmail.com', 'role': 'admin'}})
print(resp)