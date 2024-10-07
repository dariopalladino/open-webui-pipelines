# Building Open WebUI Pipelines
A set of pipelines fully integrated with Fabric Patterns that can help implementing wonderful RAGs within Open WebUI.

## Ground knowledge
Welcome to **Pipelines**, an [Open WebUI](https://github.com/open-webui) initiative. Pipelines bring modular, customizable workflows to any UI client supporting 

## 🚀 Why Choose this implementation of Pipelines?
- You can customize your RAG and enhance the capabilities of your Open WebUI installation
- The Pipelines are fully integrated with **[Fabric](https://github.com/danielmiessler/fabric?tab=readme-ov-file#fabric)**

## Youtube Transcript downloader
This pipeline integrates with Fabric so that after the transcript is extracted, a proper pattern from Fabric can be applied
Current PATTERNS available:
- SUMMARIZE
- EXTRACT_WISDOM

## Installation
- You need to have a Pipeline server up and running **[Open WebUI Pipelines](https://github.com/open-webui/pipelines/tree/main)**
- From Admin Setting in Open WebUI UI, go to Pipelines
- Install from Github URL, paste the url to the download_youtube_transcript.py github [link](https://github.com/dariopalladino/open-webui-pipelines/blob/main/download_youtube_transcripts.py)
- Go to your Chat and select the new model **YouTube Downloader Pipeline**
- Paste the YouTube URL prefixed with following available keywords: 
  (use "en" for english or "it" for italian before the keyword)
    - extract wisdom **URL**
    - summarize **URL** 
    - estrai saggezza **URL**
    - riassumi **URL**

## Side Note:
- the Youtube YoutubeTranscriptReader from LLAMA-INDEX Readers uses an unofficial YouTube API which YouTube applies rate limiting to, so be careful in using this capability too much
- No need to install any python packages, however in the future I may be implementing a new Pipeline server which will include new packages (i.e. langchain_community, etc..) so that more generic RAGs can be created

**More features to come soon... maybe!**

**Enjoy!**