"""
Ray Job entrypoint: parallel mini “training” runs.

Parallelism comes from Ray scheduling multiple `@ray.remote` tasks at once
(not from explicit threading/multiprocessing in your training loop).
"""

from __future__ import annotations

import configparser
import json
import os
import sys
from pathlib import Path

import ray

WORKDIR = Path(__file__).resolve().parent


def _load_training_section() -> configparser.SectionProxy:
    cfg = configparser.ConfigParser()
    if not cfg.read(WORKDIR / "conf.ini"):
        print("ERROR: conf.ini missing from working directory", file=sys.stderr)
        sys.exit(1)
    if "training" not in cfg:
        print("ERROR: [training] section missing in conf.ini", file=sys.stderr)
        sys.exit(1)
    return cfg["training"]


def _load_seeds() -> list[int]:
    path = WORKDIR / "seeds.txt"
    if not path.is_file():
        print("ERROR: seeds.txt missing from working directory", file=sys.stderr)
        sys.exit(1)
    seeds: list[int] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            seeds.append(int(line))
    if len(seeds) < 2:
        print("ERROR: seeds.txt needs at least two integer seeds", file=sys.stderr)
        sys.exit(1)
    return seeds


def _train_impl(
    seed: int,
    epochs: int,
    batch_size: int,
    hidden_dim: int,
    lr: float,
    input_dim: int,
    output_dim: int,
) -> dict:
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = nn.Sequential(
        nn.Linear(input_dim, hidden_dim),
        nn.ReLU(),
        nn.Linear(hidden_dim, output_dim),
    ).to(device)

    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    running_loss_sum = 0.0
    steps = 0
    last_loss = 0.0

    # This could be parallelized with e.g. torch
    for _ in range(epochs):
        x = torch.randn(batch_size, input_dim, device=device)
        target = torch.randn(batch_size, output_dim, device=device)
        optimizer.zero_grad()
        pred = model(x)
        loss = loss_fn(pred, target)
        loss.backward()
        optimizer.step()
        last_loss = float(loss.detach().cpu().item())
        running_loss_sum += last_loss
        steps += 1

    with torch.no_grad():
        w_norm = float(sum(p.detach().pow(2).sum().cpu().item() for p in model.parameters()) ** 0.5)

    out = {
        "seed": seed,
        "device": str(device),
        "epochs": epochs,
        "steps": steps,
        "running_loss_sum": round(running_loss_sum, 6),
        "final_loss": round(last_loss, 6),
        "weight_l2_norm": round(w_norm, 6),
    }
    state = {k: v.detach().cpu().tolist() for k, v in model.state_dict().items()}
    out["state_dict_keys"] = list(state.keys())
    out["first_layer_bias_sum"] = round(sum(state["0.bias"]), 6)
    return out


_gs = os.environ.get("RAY_TRAIN_NUM_GPUS", "").strip().lower()
if _gs in ("", "0", "none", "cpu"):
    train_run = ray.remote(_train_impl)
else:
    train_run = ray.remote(num_gpus=float(_gs))(_train_impl)


def main() -> None:
    ray.init()

    sec = _load_training_section()
    epochs = int(sec["epochs"])
    batch_size = int(sec["batch_size"])
    hidden_dim = int(sec["hidden_dim"])
    lr = float(sec["lr"])
    input_dim = int(sec["input_dim"])
    output_dim = int(sec["output_dim"])

    seeds = _load_seeds()
    refs = [
        train_run.remote(
            seed=s,
            epochs=epochs,
            batch_size=batch_size,
            hidden_dim=hidden_dim,
            lr=lr,
            input_dim=input_dim,
            output_dim=output_dim,
        )
        for s in seeds
    ]
    results = ray.get(refs)

    payload = {
        "runs": results,
        "sources": {
            "conf_ini": str(WORKDIR / "conf.ini"),
            "seeds_txt": str(WORKDIR / "seeds.txt"),
        },
        "ray_train_num_gpus_env": os.environ.get("RAY_TRAIN_NUM_GPUS", ""),
    }
    out_path = WORKDIR / "results.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
