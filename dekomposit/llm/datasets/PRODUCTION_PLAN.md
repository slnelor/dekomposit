# Production-Ready AutoML Translation Dataset Pipeline

Complete guide for generating, reviewing, and deploying high-quality translation datasets for Google AutoML Translation.

## Overview

**Goal:** Create 12 custom translation models (EN/RU/UK/SK in all directions) with 5,000 high-quality pairs per direction.

**Total dataset:** 60,000 translation pairs  
**Timeline:** ~1-2 weeks (generation + review)  
**Cost estimate:** $1.35 - $54 depending on model choice

---

## Phase 1: Data Generation (Automated)

### 1.1 Generate Synthetic Pairs

```bash
# Activate environment
source .venv/bin/activate

# Generate 5,000 pairs per direction (12 directions = 60,000 total)
python -m dekomposit.llm.datasets.translation_data_gen
```

**What happens:**
- Reads rules and examples from `TRANSLATION.md`
- Generates pairs for all 12 directions concurrently
- Saves to:
  - `synthetic_translations_all.json` (Pydantic models)
  - `automl/*.tsv` (one per direction, AutoML-ready)

**Time:** ~5-10 minutes (with gpt-5-nano)  
**Cost:** $1.35 (gpt-5-nano) to $54 (claude-sonnet-4.5)

### 1.2 Model Selection (Cost vs Quality)

| Model | Input | Output | Total Cost | Quality | Speed |
|-------|-------|--------|------------|---------|-------|
| **gpt-5-nano** | $0.05/1M | $0.40/1M | **$1.35** | Good | Fast ⚡ |
| **gpt-4.1-nano** | $0.10/1M | $0.40/1M | $1.50 | Good | Fast |
| **gemini-3-flash** | $0.25/1M | $1.50/1M | $5.25 | Very Good | Fast |
| **gpt-5-mini** | $0.25/1M | $2.00/1M | $6.75 | Excellent | Medium |
| **claude-sonnet-4.5** | $3.00/1M | $15.00/1M | $54.00 | Best | Slower |

**Recommendation for production:**
- **Development/Testing:** gpt-5-nano ($1.35)
- **Production:** gemini-3-flash ($5.25) or gpt-5-mini ($6.75)

---

## Phase 2: Human Review (Interactive)

### 2.1 Review Pairs

```bash
# Launch interactive review CLI
python -m dekomposit.llm.datasets.review_pairs
```

**Workflow:**
1. Select direction (e.g., EN→RU)
2. Review batches of 10 pairs
3. Approve (`a`), deny (`d`), or edit (`e`)
4. Navigate with `n` (next), `p` (previous)
5. Track progress with `s` (statistics)
6. Quit anytime (`q`) - progress auto-saves

**Review speed:** ~100-200 pairs/hour (experienced reviewer)  
**Total time:** 50-100 hours for 60,000 pairs

### 2.2 Quality Checklist

For each pair, verify:
- ✅ Translation is accurate
- ✅ Tone and style match (slang, formality)
- ✅ Idioms translated naturally
- ✅ Swearing preserved if present
- ✅ URLs/IDs/numbers unchanged
- ✅ No identical source/target (unless intended)
- ✅ Length ≤200 words

### 2.3 Editing Guidelines

**When to edit:**
- Small typos in source or target
- Better word choice for idiom
- Missing punctuation

**When to reject:**
- Completely wrong translation
- Gibberish or nonsense
- Inappropriate content
- Duplicate pairs

---

## Phase 3: Dataset Finalization

### 3.1 Export Approved Pairs

After review, approved pairs are automatically saved to:
```
dekomposit/llm/datasets/automl/approved/
├── en-ru.tsv
├── ru-en.tsv
├── en-uk.tsv
├── uk-en.tsv
├── en-sk.tsv
├── sk-en.tsv
├── ru-uk.tsv
├── uk-ru.tsv
├── ru-sk.tsv
├── sk-ru.tsv
├── uk-sk.tsv
└── sk-uk.tsv
```

### 3.2 Quality Metrics

**Target thresholds:**
- ✅ Approval rate: ≥85%
- ✅ Final count per direction: ≥4,000 pairs
- ✅ Avg segment length: 10-50 words
- ✅ No duplicates (auto-checked by AutoML)

---

## Phase 4: AutoML Upload & Training

### 4.1 Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Cloud Translation API** enabled
3. **Cloud Storage bucket** created
4. **Service account** with permissions:
   - `roles/cloudtranslate.admin`
   - `roles/storage.objectAdmin`

### 4.2 Upload TSV Files

```bash
# Create Cloud Storage bucket (one-time)
gsutil mb -l us-central1 gs://YOUR-BUCKET-NAME

# Upload all approved TSV files
gsutil -m cp automl/approved/*.tsv gs://YOUR-BUCKET-NAME/datasets/
```

### 4.3 Create Datasets (via API or Console)

**Option A: Google Cloud Console**
1. Go to [Cloud Translation](https://console.cloud.google.com/translation)
2. Click **Datasets** → **Create dataset**
3. Choose source/target languages
4. Upload TSV from Cloud Storage
5. Let AutoML auto-split (80/10/10)
6. Repeat for all 12 directions

**Option B: REST API**
```bash
# Example: Create EN→RU dataset
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "en-ru-production-v1",
    "source_language_code": "en",
    "target_language_code": "ru"
  }' \
  "https://translation.googleapis.com/v3/projects/YOUR-PROJECT/locations/us-central1/datasets"

# Then import data
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "input_config": {
      "input_files": [{
        "gcs_source": {
          "input_uris": "gs://YOUR-BUCKET/datasets/en-ru.tsv"
        }
      }]
    }
  }' \
  "https://translation.googleapis.com/v3/projects/YOUR-PROJECT/locations/us-central1/datasets/DATASET-ID:importData"
```

### 4.4 Train Models

**Per direction:**
1. Wait for dataset import to complete
2. Navigate to dataset in console
3. Click **Train** tab → **Start Training**
4. Name model (e.g., `en-ru-v1-5k`)
5. Training takes **2-8 hours** per model

**Total training time:** 24-96 hours for all 12 models

### 4.5 Training Costs

**AutoML Translation pricing (us-central1):**
- Training: ~$45-75 per model
- **Total for 12 models:** $540-900

**Note:** Models must be retrained every 18 months.

---

## Phase 5: Evaluation & Deployment

### 5.1 Model Evaluation

AutoML provides **BLEU scores** automatically:
- **Baseline (Google NMT):** ~25-35 BLEU
- **Good custom model:** ≥30 BLEU
- **Excellent custom model:** ≥35 BLEU

### 5.2 A/B Testing

Compare custom model vs baseline:
1. Select 100 test sentences
2. Translate with both models
3. Human evaluation (5-point scale)
4. Choose best model per direction

### 5.3 Production Deployment

**Use custom model in API:**
```python
from google.cloud import translate_v3

client = translate_v3.TranslationServiceClient()
parent = "projects/YOUR-PROJECT/locations/us-central1"
model = f"{parent}/models/YOUR-MODEL-ID"

response = client.translate_text(
    request={
        "parent": parent,
        "contents": ["Hello, world!"],
        "source_language_code": "en",
        "target_language_code": "ru",
        "model": model,  # Use custom model
    }
)

print(response.translations[0].translated_text)
```

---

## Maintenance & Iteration

### Ongoing Tasks

1. **Monitor quality:** Track user feedback
2. **Collect new examples:** Add domain-specific pairs
3. **Retrain models:** Every 18 months (AutoML requirement)
4. **Expand languages:** Add new directions as needed

### Version Control

Track dataset versions:
```
datasets/
├── v1_2024-02-12/
│   ├── en-ru.tsv (5000 pairs)
│   └── ...
├── v2_2024-08-15/
│   ├── en-ru.tsv (7500 pairs, added tech terms)
│   └── ...
└── v3_2025-02-12/
    ├── en-ru.tsv (10000 pairs, retrained)
    └── ...
```

---

## Cost Summary

| Phase | Component | Cost |
|-------|-----------|------|
| **Generation** | LLM API (gpt-5-nano) | $1.35 |
| **Review** | Human time (100 hrs × $15/hr) | $1,500 |
| **Storage** | Cloud Storage (negligible) | $0.10/month |
| **Training** | AutoML (12 models) | $540-900 |
| **Inference** | Per 1M characters | $20/1M chars |
| **Total (one-time)** | | **$2,041-2,401** |
| **Monthly (production)** | Depends on volume | Variable |

---

## Success Criteria

✅ **Dataset quality:**
- ≥4,000 approved pairs per direction
- ≥85% approval rate
- No duplicates or identical source/target

✅ **Model quality:**
- BLEU score ≥30 (better than baseline)
- Human eval ≥4/5 on average
- Natural-sounding translations

✅ **Production readiness:**
- All 12 models trained and deployed
- API integration tested
- Monitoring in place

---

## Next Steps

1. ✅ Generate initial dataset (complete)
2. ⏳ Review and approve pairs (start here)
3. ⏳ Upload to AutoML
4. ⏳ Train models
5. ⏳ Evaluate and deploy

**Ready to start?**
```bash
python -m dekomposit.llm.datasets.review_pairs
```
