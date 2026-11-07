from pathlib import Path

import allel
import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline

HERE = Path(__file__).parent
DATA = HERE / "data"
VCF = DATA / "chr22.vcf.gz"
PANEL = DATA / "panel.txt"
MODEL_OUT = HERE / "model.joblib"
PER_CHUNK = 1000  # variants kept from each 50k-variant chunk


def load_genotypes():
    fields = [
        "variants/POS",
        "variants/REF",
        "variants/ALT",
        "variants/is_snp",
        "calldata/GT",
    ]
    _, samples, _, chunks = allel.iter_vcf_chunks(
        str(VCF), fields=fields, alt_number=3, chunk_length=50000
    )

    blocks, positions, refs, alts = [], [], [], []
    for chunk, _, _, _ in chunks:
        alt = chunk["variants/ALT"]
        keep = chunk["variants/is_snp"] & (alt[:, 1] == "")  # biallelic SNPs only

        dosage = allel.GenotypeArray(chunk["calldata/GT"]).to_n_alt()  # variants x samples
        freq = dosage.mean(axis=1) / 2
        keep &= (freq >= 0.05) & (freq <= 0.95)  # drop rare variants

        idx = np.where(keep)[0]
        if len(idx) > PER_CHUNK:
            idx = idx[np.linspace(0, len(idx) - 1, PER_CHUNK).astype(int)]

        blocks.append(dosage[idx].T.astype(np.float32))
        positions.append(chunk["variants/POS"][idx])
        refs.append(chunk["variants/REF"][idx])
        alts.append(alt[idx, 0])
        print(f"processed chunk, features so far: {sum(b.shape[1] for b in blocks)}")

    return (
        np.hstack(blocks),
        np.concatenate(positions),
        np.concatenate(refs),
        np.concatenate(alts),
        samples,
    )


def write_test_files(X, positions, refs, alts, y):
    """Write one fake 23andMe-style file per population, for testing the API."""
    for pop in np.unique(y):
        i = int(np.where(y == pop)[0][0])
        lines = ["# rsid\tchromosome\tposition\tgenotype"]
        for j in range(X.shape[1]):
            r, a, d = str(refs[j]), str(alts[j]), int(X[i, j])
            g = r + r if d == 0 else (r + a if d == 1 else a + a)
            lines.append(f"rs{j}\t22\t{positions[j]}\t{g}")
        (DATA / f"test_{pop}.txt").write_text("\n".join(lines) + "\n")
        print(f"wrote data/test_{pop}.txt")


def main():
    X, positions, refs, alts, samples = load_genotypes()

    panel = pd.read_csv(PANEL, sep="\t").set_index("sample")
    y = panel.loc[samples, "super_pop"].values

    print(f"Training matrix: {X.shape[0]} people x {X.shape[1]} variants")

    pipe = Pipeline(
        [
            ("pca", PCA(n_components=10)),
            ("clf", LogisticRegression(max_iter=2000)),
        ]
    )

    scores = cross_val_score(pipe, X, y, cv=5)
    print(f"5-fold CV accuracy: {scores.mean():.3f} (+/- {scores.std():.3f})")

    pipe.fit(X, y)
    joblib.dump(
        {
            "pipeline": pipe,
            "positions": positions,
            "refs": refs,
            "alts": alts,
            "means": X.mean(axis=0),
            "classes": list(pipe.classes_),
        },
        MODEL_OUT,
    )
    print(f"Saved {MODEL_OUT}")

    write_test_files(X, positions, refs, alts, y)


if __name__ == "__main__":
    main()