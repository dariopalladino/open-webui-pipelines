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

## BBC Daily Digest
This pipeline integrates with Fabric so that after the transcript is extracted, a proper pattern from Fabric can be applied
Current PATTERNS available:
- SUMMARIZE
This pipelines can be activated with asking a simple: "Give me the daily digest"
Once you get the list of articles available for that day, you can grab the link provided to the article you want more insights from and ask for:
summarize this **URL**

## Installation
- You need to have a Pipeline server up and running **[Open WebUI Pipelines](https://github.com/open-webui/pipelines/tree/main)**
- From Admin Setting in Open WebUI UI, go to Pipelines
- Install from Github URL, paste the url to the download_youtube_transcript.py github [link](https://github.com/dariopalladino/open-webui-pipelines/blob/main/download_youtube_transcripts.py)
- Go to your Chat and select the new model **YouTube Transcript Generator Pipeline**
- Paste the YouTube URL prefixed with following available keywords: 
  (use "en" for english or "it" for italian before the keyword)
    - extract wisdom **URL**
    - summarize **URL** 
    - estrai saggezza **URL**
    - riassumi **URL**
or 
- Go to your Chat and select the new model **BBC News Daily Digest Pipeline**
- Ask: "Give me a daily digest" and the output will be a list of articles with description and link
- Grab any link and ask: 
  (use "en" for english or "it" for italian before the keyword)
    - summarize **URL** 
    - riassumi **URL**

## Side Notes:
- the Youtube YoutubeTranscriptReader from LLAMA-INDEX Readers uses an unofficial YouTube API which YouTube applies rate limiting to, so be careful in using this capability too much
- No need to install any python packages, however in the future I may be implementing a new Pipeline server which will include new packages (i.e. langchain_community, etc..) so that more generic RAGs can be created
- JFYI - The BBC News Digest uses the XMLTree to parse the XML from BBC, thus since this is vulnerable to various attacks, it might be helpful some help to mitigate this drawback. To yield the attack, a MITM should be able to inject code in the XML content you're going to parse, which is very unlikely but can happen! 

**More features to come soon... maybe!**

**Enjoy!**