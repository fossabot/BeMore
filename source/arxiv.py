import feedparser
import argparse


def main(args: argparse.Namespace):
    d = feedparser.parse("http://arxiv.org/rss/cs")
    papers = []
    for entry in d.entries:
        try:
            author = [
                i.split(">")[1].split("<")[0] for i in entry["author"].split(", ")
            ]
        except IndexError:
            author = [entry["author"].split(">")[1].split("<")[0]]
        papers.append(
            {
                "title": entry["title"].split("(")[0].strip(),
                "url": entry["link"],
                "abstract": entry["summary"].replace("<p>", "").replace("</p>", ""),
                "authors": ", ".join(author),
            }
        )

    import json

    with open(args.output, "w") as f:
        json.dump(papers, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="arxiv spider")
    parser.add_argument("--output", type=str, default="arxiv.json")
    args = parser.parse_args()
    main(args)
