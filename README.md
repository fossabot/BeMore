# BeMore

This is a recommendation system for researchers to find specific papers that are related to their research interests. The system is based on the NLP zero-shot classification model.

## Setup

```bash
pip install feedparser
```

Crawl arxiv papers, run the following command:

```bash
python source/Arxiv.py
```

Generate the recommend papers

```bash
python recommend.py
```