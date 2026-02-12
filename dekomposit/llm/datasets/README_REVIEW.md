# Translation Pair Review Tool

Interactive CLI for reviewing and approving generated translation pairs before uploading to AutoML Translation.

## Features

- ✅ **Batch review** - Review 10 pairs at a time
- ✅ **Fast keyboard navigation** - No mouse needed
- ✅ **Inline editing** - Fix translations on the fly
- ✅ **Resume support** - Stop and continue anytime
- ✅ **Statistics tracking** - See approval progress
- ✅ **Auto-save** - Progress saved automatically

## Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Run review tool
python -m dekomposit.llm.datasets.review_pairs
```

## Keyboard Commands

| Key | Action |
|-----|--------|
| `a` | Approve all pairs in current batch |
| `d` | Deny all pairs in current batch |
| `1-0` | Toggle approve/deny for specific pair (1-10) |
| `e` | Edit a pair (opens inline editor) |
| `n` | Next batch |
| `p` | Previous batch |
| `s` | Show statistics |
| `h` | Show help |
| `q` | Save and quit |

## Workflow

1. **Select direction** - Choose from 12 language directions (EN/RU/UK/SK)
2. **Review batch** - See 10 pairs with source and target
3. **Approve/reject** - Use keyboard shortcuts
4. **Edit if needed** - Fix any errors inline
5. **Move to next** - Auto-saves progress
6. **Repeat** - Continue until all pairs reviewed

## Output Files

After review, approved/rejected pairs are saved to:

```
dekomposit/llm/datasets/
├── automl/
│   ├── approved/
│   │   ├── en-ru.tsv
│   │   ├── ru-en.tsv
│   │   └── ... (12 files)
│   └── rejected/
│       ├── en-ru.tsv
│       └── ... (12 files)
└── review_state/
    ├── en-ru.json  (resume state)
    └── ...
```

## Cost Estimate

**For 5,000 pairs per direction (60,000 total):**

| Model | Total Cost |
|-------|------------|
| gpt-5-nano | **$1.35** ⭐ Best value |
| gpt-4.1-nano | $1.50 |
| gemini-3-flash | $5.25 |
| gpt-5-mini | $6.75 |
| claude-sonnet-4.5 | $54.00 |

**Recommendation:** Use `gpt-5-nano` for bulk generation.

## Tips

- Use `a` to quickly approve good batches
- Use `e` to fix small errors instead of rejecting
- Check statistics (`s`) regularly to track progress
- Edited pairs are automatically approved
- Progress saves automatically - safe to quit anytime

## Example Session

```
1. Run: python -m dekomposit.llm.datasets.review_pairs
2. Select: "1" for EN→RU
3. Review batch 1/500
4. Press "a" to approve all
5. Press "n" for next batch
6. Press "e" to edit pair #3
7. Press "s" to see stats (10 approved, 0 rejected)
8. Press "q" to save and quit
```

## Next Steps

After review:
1. Upload approved TSV files to Google Cloud Storage
2. Create AutoML dataset per direction
3. Train custom models
4. Evaluate BLEU scores
5. Deploy to production
