# Artwork

All images were generated with **Higgsfield** (MCP tool `generate_image_batch`, model **Recraft V4.1**, `model_type: standard`) during the hackathon. Exact prompts, job ids, sizes and download URLs are in [`higgsfield_manifest.json`](higgsfield_manifest.json).

| File | Size | Used in | Alt text |
|---|---|---|---|
| `generated/hero_banner.png` | 16:9, 2k | Formerly the header background; the redesigned start page uses a live demo instead. Kept as a video B-roll start frame | (none, decorative) |
| `generated/level1_invisible_ink.png` | 1:1, 1k | Level 1 header | A qubit splits into a blue and an orange path; a faint painted phase on the orange path only shows up as ripples where the paths meet again. |
| `generated/level2_dark_port.png` | 1:1, 1k | Level 2 header | An interferometer with a violet mystery crystal on one path; one output detector glows, the other is completely dark. |
| `generated/level3_eraser.png` | 1:1, 1k | Level 3 header | A small eye-shaped detector watches two light paths while an eraser wipes away its line of sight and interference ripples return. |
| `generated/video_title_bg.png` | 16:9, 2k | Demo video title/outro | (video only) |
| `generated/video_arrows_explainer.png` | 16:9, 2k | Demo video cut-in | (video only) |

Video clips (Higgsfield `generate_video_batch`, model **Kling 3.0**, 5 s, silent, start frame = the image above): `title_card` (job `22a0aaad-f1fd-473f-811d-ed501b8a5b8b`) and `arrows_explainer` (job `7b490f88-644a-4d36-a287-a00fec3cce48`).

The second demo cut uses four newer clips drawn from the game's own art (Kling 3.0 with start and end keyframes, plus one exact animation): see `demo_video_v2` in the manifest and [docs/VIDEO_SCRIPT.md](../docs/VIDEO_SCRIPT.md#higgsfield-assets).

## Style

Flat, minimal vector look with quantum motifs (two paths, beam splitters, ripples), "no text" in every prompt, and the game's palette passed as `colors`:

`#0B1020` navy · `#141B34` panel · `#4EA8FF` upper path (blue) · `#FFB000` lower path (amber) · `#5CE1E6` accent (cyan) · `#B48CFF` mystery (violet) · `#E8ECF8` text.

## Putting the images into the game

The page does not load loose image files (Qollab serves JS modules reliably, plain assets less so). Instead, `tools/embed_art.py` converts the web images to small WebP files and writes them into `web/art-data.js` as data URIs (about 190 KiB in total, well under Qollab's 2 MB per-file limit):

```bash
pip install pillow
python tools/embed_art.py          # downloads the files listed in the manifest, then embeds them
python tools/embed_art.py --offline  # if you saved the PNGs into assets/generated/ yourself
```

Until then, `web/art.js` draws simple SVG emblems with the same alt text, so the game looks finished either way. Levels 4 (Kickback) and 5 (Amplifier) only have SVG emblems so far; to give them images, add prompts to the manifest in the same style and re-run the tool.

> The build environment used for this repository could not reach Higgsfield's CDN (`d8j0ntlcm91z4.cloudfront.net`), so the PNGs are not committed yet. Run the command above on your machine, or download them from your Higgsfield library into `assets/generated/` with the file names in the table.

## Regenerating

Ask your assistant to call Higgsfield MCP `generate_image` (or `generate_image_batch` for several) with the manifest's `model`, `aspect_ratio`, `resolution`, `colors`, `background_color` and `prompt`. Preflight the cost with `get_cost: true` (about 1.25 credits per Recraft image). Update the job id and URL in the manifest, then re-run `tools/embed_art.py`.
