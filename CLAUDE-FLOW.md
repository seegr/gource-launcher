# CLAUDE-FLOW.md

## Session 2025-11-21 (update)

### Hotovo ✅
- Google Fonts integrace - fuzzy výběr 1500+ fontů, cache v ~/.cache/gource-fonts/
- Default font: Fira Code Regular (lokální)
- GitHub repos integrace - fetch přes `gh repo list`, clone do cache, auto-cleanup po ukončení
- Interaktivní directory browser - navigace šipkami, 🎯 git repos, 📁 složky
- Vylepšené font nastavení: dir-font-size 18, user-font-size 24, user-scale 1.5
- filename-time 2 (rychlejší fade názvů souborů)
- Clear console před spuštěním
- Hinty pro klávesové zkratky gource

### Default gource nastavení
- Rychlost: 2 sec/day
- Fullscreen: true
- Auto-skip: 3 sec
- Title: název projektu
- Camera: overview
- Font: Fira Code Regular
- Dir font: 18, User font: 24, User scale: 1.5

### Custom menu (zjednodušené)
- Rychlost, Fullscreen, Hide elements, Camera mode, Google Font

### Závislosti
```bash
pip install InquirerPy python-dotenv requests
brew install gource gh
```

### .env
```
GOOGLE_FONTS_API_KEY=xxx
```

### Spuštění
```bash
python main.py
```

### TODO
- Cross-platform podpora (Windows: `cls` místo `clear`, jiný sound player)
- GitHub Actions pro multi-platform buildy (macOS, Windows, Linux)

---
*Gource is king! 👑*
