import json
from typing import Dict, List
from transformers import pipeline
from tqdm import tqdm

import numpy as np

# use huggingface
# classifier = pipeline(
#     "zero-shot-classification",
#     model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
#     device="cuda",
# )
classifier = pipeline("zero-shot-classification", model="model", device="cuda")
candidate_labels = [
    "Federated learning",
    "Adversarial Attack",
    "Logic in Computer Science",
    "zero-shot",
    "Backdoor Attack",
    "Neural Collapse",
    "Mobile Edge Computing",
    "Multi-objective optimization",
    "Pareto Sets",
    "Quantitative Finance",
    "Physics-informed neural networks",
    "Discrete Mathematics",
    "Blockchains",
    "Computational Physics",
    "Diffusion models",
    "Distributional Reinforcement Learning",
    "Parameter efficient fine-tuning",
    "Distillation methods",
    "Reinforcement Learning",
    "Multimodal",
]


offset_sample = []
output_json = {}
with open("arxiv.json") as f:
    data: List[Dict] = json.load(f)
    for item in tqdm(data):
        abstract: str = item["title"] + ": " + item["abstract"].replace("\n", " ")
        output = classifier(abstract, candidate_labels, multi_label=True)
        if np.all(np.array(output["scores"]) < 0.5):  # type: ignore
            offset_sample.append(
                output
            )  # offset_sample means the sample that the model is not confident
            continue

        if output["scores"][0] < 0.85:  # type: ignore
            continue  # The sample is controversial

        try:
            output_json[output["labels"][0]].append({"url": item["url"], "sequence": output["sequence"], "score": output["scores"][0]})  # type: ignore
        except KeyError:
            output_json[output["labels"][0]] = [  # type: ignore
                {"url": item["url"], "sequence": output["sequence"], "score": output["scores"][0]}  # type: ignore
            ]

with open("offset_sample.json", "w") as f:
    json.dump(offset_sample, f, indent=4)

with open("output.json", "w") as f:
    json.dump(output_json, f, indent=4)
