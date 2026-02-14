# Translation Pair Review Tool

Interactive CLI for reviewing and approving generated translation pairs before uploading to AutoML Translation.

## Features

- ✅ **Batch review** - Review 4 pairs at a time (optimized for readability)
- ✅ **Lightning-fast workflow** - SPACE to approve & advance
- ✅ **Smart editing** - Edit source, target, or both without copy/paste
- ✅ **Quality warnings** - Auto-detect declination and grammar issues
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

### Quick Actions (Most Used)
| Key | Action |
|-----|--------|
| `SPACE` or `ENTER` | **Approve all & go to next batch** ⚡ |
| `x` | Reject all & go to next batch |

### Individual Pairs
| Key | Action |
|-----|--------|
| `1-4` | Toggle approve/reject for specific pair |
| `e` | Edit a pair (choose: s=source, t=target, b=both) |

### Navigation
| Key | Action |
|-----|--------|
| `n` or `→` | Next batch |
| `p` or `←` | Previous batch |
| `s` | Show statistics |
| `q` | Save and quit |

## Workflow

1. **Select direction** - Choose from 12 language directions (EN/RU/UK/SK)
2. **Review batch** - See 4 pairs with source and target (+ quality warnings)
3. **Quick approve** - Hit SPACE to approve all & advance ⚡
4. **Or review individually** - Press 1-4 to toggle, or 'e' to edit
5. **Auto-saves** - Progress saved after every action
6. **Repeat** - Continue until all pairs reviewed

**Pro tip:** Most batches are good - just spam SPACE to fly through them!

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

- **SPACE is your friend** - Most batches are good, just hit SPACE to approve & advance
- Use `e` to fix typos instead of rejecting entire pairs
- Yellow warnings highlight potential issues (declination, length, etc.)
- Check statistics (`s`) to track progress
- Edited pairs are automatically approved
- Progress saves automatically - safe to quit anytime (Ctrl+C works too)

## Example Session

```
1. Run: python -m dekomposit.llm.datasets.review_pairs
2. Select: "1" for EN→RU
3. Review batch 1/500 (4 pairs shown)
4. Press SPACE to approve all & advance (instant!)
5. Batch 2/500 - press SPACE again
6. Batch 3/500 - warning shows on pair #2, press "e" → "t" to fix target
7. Press SPACE to continue
8. Press "s" to see stats (12 approved, 0 rejected)
9. Press "q" to save and quit (or Ctrl+C)
```

**Speed tip:** You can review 100+ pairs/minute by just hitting SPACE for good batches!

## Next Steps

After review:
1. Upload approved TSV files to Google Cloud Storage
2. Create AutoML dataset per direction
3. Train custom models
4. Evaluate BLEU scores
5. Deploy to production
