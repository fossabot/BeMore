import feedparser
import argparse


def main(args: argparse.Namespace):
    d = feedparser.parse("http://proceedings.mlr.press//v221/assets/rss/feed.xml")
    papers = []
    for entry in d.entries:
        papers.append(
            {
                "title": entry["title"],
                "url": entry["link"],
                "abstract": entry["description"],
            }
        )

    import json

    with open(args.output, "w") as f:
        json.dump(papers, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PMLR spider")
    parser.add_argument("--output", type=str, default="PMLR.json")
    args = parser.parse_args()
    main(args)
