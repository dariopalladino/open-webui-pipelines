# Building Open WebUI Pipelines
A pipeline fully integrated with Fabric Patterns that returns the full, detailed youtube transcript summarizations in English or Italian of a passed in youtube url.

## Ground knowledge
Welcome to **Pipelines**, an [Open WebUI](https://github.com/open-webui) initiative. Pipelines bring modular, customizable workflows to any UI client supporting 

## 🚀 Why Choose this implementation of Pipelines?
- You can customize your RAG and enhance the capabilities of your Open WebUI installation
- The Pipeline is fully integrated with [Fabric](https://github.com/danielmiessler/fabric?tab=readme-ov-file#fabric)

## Youtube Transcript downloader
The pipeline integrates with Fabric so that after the transcript is extracted, a proper pattern from Fabric can be applied
Current PATTERNS available:
- SUMMARIZE
- EXTRACT_WISDOM

## Installation
- From Admin Setting in Open WebUI UI, go to Pipelines
- Install from Github URL, paste the url to the download_youtube_transcript.py github [link](https://github.com/dariopalladino/open-webui-pipelines/blob/main/download_youtube_transcripts.py)
- Go to your Chat and select the new model **YouTube Downloader Pipeline**
- paste the YouTube URL prefixed with following available keywords:
    - extract wisdom (for english)
    - summarize (for english)
    - estrai saggezza (for italian)
    - riassumi (for italian)

## Side Note:
- the Youtube YoutubeTranscriptReader from LLAMA-INDEX Readers uses an unofficial YouTube API which applies rate limiting, so be careful in using this capability too much
- No need to install any python packages, however in the future I may be implementing a new Pipeline server which will include new packages (i.e. langchain_community, etc..) so that more generic RAGs can be created

**More features to come soon**

**Enjoy!**