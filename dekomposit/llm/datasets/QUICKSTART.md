# Quick Start Guide

Get started with translation dataset generation and review in 5 minutes.

## Step 1: Generate Dataset (2 minutes)

```bash
# Activate environment
source .venv/bin/activate

# Generate 5,000 pairs per direction (60,000 total)
python -m dekomposit.llm.datasets.translation_data_gen
```

**Output:**
- `synthetic_translations_all.json` - All pairs as Pydantic models
- `automl/*.tsv` - 12 TSV files (one per direction)

**Cost:** $1.35 with gpt-5-nano

---

## Step 2: Review Pairs (Start Now)

```bash
# Launch interactive review tool
python -m dekomposit.llm.datasets.review_pairs
```

**Quick commands:**
- `a` = approve all
- `d` = deny all
- `1-9` = toggle individual pair
- `e` = edit pair
- `n` = next batch
- `q` = quit (auto-saves)

---

## Step 3: Upload to AutoML (After Review)

```bash
# Create bucket (one-time)
gsutil mb -l us-central1 gs://YOUR-BUCKET-NAME

# Upload approved TSVs
gsutil -m cp automl/approved/*.tsv gs://YOUR-BUCKET-NAME/datasets/
```

Then create datasets in [Google Cloud Console](https://console.cloud.google.com/translation).

---

## Cost Estimate

**For 60,000 pairs total (5k per direction × 12):**

| Component | Cost |
|-----------|------|
| Generation (gpt-5-nano) | $1.35 |
| Review (100 hrs @ $15/hr) | $1,500 |
| AutoML Training (12 models) | $540-900 |
| **Total** | **$2,041-2,401** |

---

## What's Included?

✅ **12 language directions:**
- English ↔ Russian
- English ↔ Ukrainian  
- English ↔ Slovak
- Russian ↔ Ukrainian
- Russian ↔ Slovak
- Ukrainian ↔ Slovak

✅ **High-quality examples:**
- 140+ native-speaker examples in `TRANSLATION.md`
- Slang, idioms, swearing, cultural references
- Natural casual speech
- URLs, IDs, brand names preserved

✅ **Production-ready pipeline:**
- Async generation (3x faster)
- Rich-based review CLI
- AutoML-compatible TSV output
- Resume support (never lose progress)

---

## Files

```
dekomposit/llm/datasets/
├── QUICKSTART.md               ← You are here
├── PRODUCTION_PLAN.md          ← Full guide
├── README_REVIEW.md            ← Review CLI docs
├── TRANSLATION.md              ← Rules + examples
├── translation_data_gen.py     ← Generator
├── review_pairs.py             ← Review CLI
├── synthetic_translations_all.json
├── automl/
│   ├── approved/               ← Final TSVs
│   └── rejected/
└── review_state/               ← Resume data
```

---

## Support

- **Issues?** Check `PRODUCTION_PLAN.md` for detailed instructions
- **Questions?** Review `README_REVIEW.md` for CLI help
- **Examples?** See `TRANSLATION.md` for quality guidelines

---

## Ready?

```bash
# Start reviewing now
python -m dekomposit.llm.datasets.review_pairs
```

Good luck! 🚀
