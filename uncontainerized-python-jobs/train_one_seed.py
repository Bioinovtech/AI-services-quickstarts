from __future__ import annotations

import configparser
import json
import os
from pathlib import Path

import torch
import torch.nn as nn


WORKDIR = Path(__file__).resolve().parent


def load_seed() -> int:
    index = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
    seeds = [
        int(line.strip())
        for line in (WORKDIR / "seeds.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if index >= len(seeds):
        raise ValueError(f"JOB_COMPLETION_INDEX={index} has no matching seed")
    return seeds[index]


def load_config() -> dict[str, float | int]:
    cfg = configparser.ConfigParser()
    cfg.read(WORKDIR / "conf.ini")
    training = cfg["training"]
    return {
        "epochs": training.getint("epochs"),
        "batch_size": training.getint("batch_size"),
        "hidden_dim": training.getint("hidden_dim"),
        "lr": training.getfloat("lr"),
        "input_dim": training.getint("input_dim"),
        "output_dim": training.getint("output_dim"),
    }


def main() -> None:
    seed = load_seed()
    cfg = load_config()
    torch.manual_seed(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = nn.Sequential(
        nn.Linear(int(cfg["input_dim"]), int(cfg["hidden_dim"])),
        nn.ReLU(),
        nn.Linear(int(cfg["hidden_dim"]), int(cfg["output_dim"])),
    ).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=float(cfg["lr"]))
    loss_fn = nn.MSELoss()

    running_loss_sum = 0.0
    last_loss = 0.0
    for _ in range(int(cfg["epochs"])):
        x = torch.randn(int(cfg["batch_size"]), int(cfg["input_dim"]), device=device)
        y = torch.randn(int(cfg["batch_size"]), int(cfg["output_dim"]), device=device)
        optimizer.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        optimizer.step()
        last_loss = float(loss.detach().cpu().item())
        running_loss_sum += last_loss

    weight_l2_norm = float(sum(p.detach().pow(2).sum().cpu().item() for p in model.parameters()) ** 0.5)
    print(
        json.dumps(
            {
                "completion_index": int(os.environ.get("JOB_COMPLETION_INDEX", "0")),
                "seed": seed,
                "device": str(device),
                "epochs": int(cfg["epochs"]),
                "running_loss_sum": round(running_loss_sum, 6),
                "final_loss": round(last_loss, 6),
                "weight_l2_norm": round(weight_l2_norm, 6),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
