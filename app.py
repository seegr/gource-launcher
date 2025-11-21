#!/usr/bin/env python3
import os
import sys
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv
from InquirerPy import inquirer

load_dotenv(Path(__file__).parent / '.env')

FONTS_CACHE_DIR = Path.home() / '.cache' / 'gource-fonts'
REPOS_CACHE_DIR = Path.home() / '.cache' / 'gource-repos'
GOOGLE_FONTS_API_KEY = os.getenv('GOOGLE_FONTS_API_KEY')
DEFAULT_FONT = Path(__file__).parent / 'fonts' / 'Fira_Code' / 'FiraCode-Regular.ttf'


def fetch_google_fonts():
    """Načte seznam Google Fonts z API"""
    if not GOOGLE_FONTS_API_KEY:
        print("⚠️  GOOGLE_FONTS_API_KEY není nastaven v .env")
        return []

    url = f"https://www.googleapis.com/webfonts/v1/webfonts?key={GOOGLE_FONTS_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('items', [])
    except requests.RequestException as e:
        print(f"❌ Chyba při načítání fontů: {e}")
        return []


def download_font(font_data):
    """Stáhne font do cache a vrátí cestu k TTF souboru"""
    FONTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    family = font_data['family']
    # Preferuj regular variantu
    files = font_data.get('files', {})
    ttf_url = files.get('regular') or list(files.values())[0] if files else None

    if not ttf_url:
        return None

    # Sanitize filename
    filename = family.replace(' ', '_') + '.ttf'
    filepath = FONTS_CACHE_DIR / filename

    # Použij cache pokud existuje
    if filepath.exists():
        return str(filepath)

    try:
        print(f"⏬ Stahuji font {family}...")
        response = requests.get(ttf_url, timeout=30)
        response.raise_for_status()
        filepath.write_bytes(response.content)
        return str(filepath)
    except requests.RequestException as e:
        print(f"❌ Chyba při stahování fontu: {e}")
        return None


def select_google_font():
    """Zobrazí fuzzy výběr Google fontů a vrátí cestu k TTF"""
    fonts = fetch_google_fonts()
    if not fonts:
        return None

    # Připrav choices pro fuzzy search
    font_choices = [f['family'] for f in fonts]
    font_map = {f['family']: f for f in fonts}

    selected = inquirer.fuzzy(
        message="Vyber Google Font (piš pro filtrování):",
        choices=['[Systémový font]'] + font_choices,
        default="",
    ).execute()

    if selected == '[Systémový font]' or selected is None:
        return None

    font_data = font_map.get(selected)
    if font_data:
        return download_font(font_data)
    return None


def fetch_github_repos():
    """Načte seznam GitHub repozitářů přes gh CLI"""
    try:
        result = subprocess.run(
            ['gh', 'repo', 'list', '--limit', '200', '--json', 'nameWithOwner,name'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"❌ Chyba při načítání GitHub repos: {result.stderr}")
            return []
        import json
        repos = json.loads(result.stdout)
        return repos
    except FileNotFoundError:
        print("❌ gh CLI není nainstalované!")
        return []
    except Exception as e:
        print(f"❌ Chyba: {e}")
        return []


def clone_repo(repo_full_name):
    """Naklonuje repo do cache"""
    REPOS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    repo_dir = REPOS_CACHE_DIR / repo_full_name.replace('/', '_')

    # Vždy čerstvý clone
    if repo_dir.exists():
        import shutil
        shutil.rmtree(repo_dir)

    print(f"📥 Klonuji {repo_full_name}...")
    result = subprocess.run(
        ['gh', 'repo', 'clone', repo_full_name, str(repo_dir)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ Chyba při klonování: {result.stderr}")
        return None

    return str(repo_dir)


def cleanup_repo(repo_path):
    """Smaže repo z cache"""
    import shutil
    if repo_path and Path(repo_path).exists():
        shutil.rmtree(repo_path)
        print("🧹 Cache vyčištěna.")


def select_github_repo():
    """Zobrazí fuzzy výběr GitHub repozitářů"""
    repos = fetch_github_repos()
    if not repos:
        return None, None

    choices = [r['nameWithOwner'] for r in repos]

    selected = inquirer.fuzzy(
        message="Vyber GitHub repo (piš pro filtrování):",
        choices=choices,
        default="",
    ).execute()

    if selected is None:
        return None, None

    repo_path = clone_repo(selected)
    repo_name = selected.split('/')[-1]

    return repo_path, repo_name


def browse_for_git_repo(start_path=None):
    """Interaktivní procházení složek - zobrazuje jen git repozitáře"""
    current = Path(start_path or os.getcwd()).resolve()

    while True:
        try:
            all_dirs = sorted([d for d in current.iterdir() if d.is_dir() and not d.name.startswith('.')])
        except PermissionError:
            all_dirs = []

        # Rozděl na git repos a navigační složky
        git_repos = [d.name for d in all_dirs if (d / '.git').exists()]
        nav_dirs = [d.name for d in all_dirs if not (d / '.git').exists()]

        choices = ['⬆️  ..']
        choices += [f'🎯 {r}' for r in git_repos]  # Git repos
        choices += [f'📁 {d}' for d in nav_dirs]   # Navigace

        result = inquirer.fuzzy(
            message=f"{current}",
            choices=choices,
        ).execute()

        if result is None:
            return None, None
        elif result == '⬆️  ..':
            current = current.parent
        elif result.startswith('🎯 '):
            # Vybrán git repo
            repo_name = result.replace('🎯 ', '')
            return str(current / repo_name), repo_name
        else:
            # Navigace do složky
            folder = result.replace('📁 ', '')
            current = current / folder


def find_git_projects(base_path):
    """Najde všechny složky s .git v base_path"""
    projects = []

    if not os.path.exists(base_path):
        print(f"Složka {base_path} neexistuje!")
        return projects

    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            git_path = os.path.join(item_path, '.git')
            if os.path.exists(git_path):
                projects.append(item)

    return sorted(projects)


def get_gource_settings(project_name, use_defaults=True):
    """Vrátí nastavení pro gource"""
    settings = {
        'seconds_per_day': 2,
        'fullscreen': True,
        'auto_skip': 3,
        'title': project_name,
        'hide': [],
        'camera_mode': 'overview',
        'loop': False,
        'font_file': str(DEFAULT_FONT) if DEFAULT_FONT.exists() else None,
        'dir_font_size': 18,
        'user_font_size': 24,
        'user_scale': 1.5,
        'filename_time': 2,
    }

    if not use_defaults:
        # Rychlost
        speed = inquirer.number(
            message="Rychlost (seconds-per-day):",
            default=2,
            min_allowed=1,
            max_allowed=100,
        ).execute()
        settings['seconds_per_day'] = speed

        # Fullscreen
        fullscreen = inquirer.confirm(
            message="Fullscreen?",
            default=True,
        ).execute()
        settings['fullscreen'] = fullscreen

        # Hide elements
        hide_options = ['date', 'usernames', 'filenames', 'dirnames', 'files', 'users']
        hide = inquirer.checkbox(
            message="Co skrýt? (mezerník pro výběr):",
            choices=hide_options,
            default=[],
        ).execute()
        settings['hide'] = hide

        # Camera mode
        camera = inquirer.select(
            message="Camera mode:",
            choices=['overview', 'track'],
            default='overview',
        ).execute()
        settings['camera_mode'] = camera

        # Google Font
        use_custom_font = inquirer.confirm(
            message="Použít Google Font?",
            default=False,
        ).execute()
        if use_custom_font:
            font_path = select_google_font()
            settings['font_file'] = font_path

    return settings


def build_gource_command(project_path, settings):
    """Sestaví gource command z nastavení"""
    cmd = ['gource', project_path]

    cmd.extend(['-s', str(settings['seconds_per_day'])])

    if settings['fullscreen']:
        cmd.append('-f')

    if settings['auto_skip'] is not None:
        cmd.extend(['-a', str(settings['auto_skip'])])
    else:
        cmd.append('--disable-auto-skip')

    cmd.extend(['--title', settings['title']])

    if settings['hide']:
        cmd.extend(['--hide', ','.join(settings['hide'])])

    cmd.extend(['--camera-mode', settings['camera_mode']])

    if settings['loop']:
        cmd.append('--loop')

    if settings.get('font_file'):
        cmd.extend(['--font-file', settings['font_file']])

    if settings.get('dir_font_size'):
        cmd.extend(['--dir-font-size', str(settings['dir_font_size'])])

    if settings.get('user_font_size'):
        cmd.extend(['--user-font-size', str(settings['user_font_size'])])

    if settings.get('user_scale'):
        cmd.extend(['--user-scale', str(settings['user_scale'])])

    if settings.get('filename_time'):
        cmd.extend(['--filename-time', str(settings['filename_time'])])

    return cmd


def run_gource(project_path, settings):
    """Spustí gource s danými nastaveními"""
    cmd = build_gource_command(project_path, settings)

    os.system('clear')
    print(f"🎬 Spouštím: {' '.join(cmd)}\n")
    print("💡 Hinty: [D] složky | [F] soubory | [U] uživatelé | [Space] pauza | [Q] konec\n")

    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print("❌ Gource není nainstalovaný! Nainstaluj ho pomocí: brew install gource")
    except KeyboardInterrupt:
        print("\n\n⏹️  Přerušeno.")


def main():
    os.system('clear')

    is_github = False
    project_path = None

    try:
        # Výběr zdroje
        source = inquirer.select(
            message="Odkud načíst projekt?",
            choices=[
                'Lokální projekty',
                'GitHub repozitáře',
                '[Zrušit]',
            ],
            default='Lokální projekty',
        ).execute()

        if source == '[Zrušit]':
            print("Čau!")
            return

        is_github = source.startswith('GitHub')

        if is_github:
            project_path, selected = select_github_repo()
            if not project_path:
                print("Čau!")
                return
        else:
            project_path, selected = browse_for_git_repo()
            if not project_path:
                print("Čau!")
                return

        print(f"\n📁 Projekt: {selected}")

        # Výběr režimu
        mode = inquirer.select(
            message="Jak chceš spustit gource?",
            choices=[
                'Default nastavení (rychlé)',
                'Custom nastavení (pokročilé)',
                '[Zrušit]',
            ],
            default='Default nastavení (rychlé)',
        ).execute()

        if mode == '[Zrušit]':
            print("Čau!")
            return

        use_defaults = mode.startswith('Default')
        settings = get_gource_settings(selected, use_defaults)

        run_gource(project_path, settings)

    except KeyboardInterrupt:
        print("\n\nPřerušeno.")
    finally:
        # Cleanup GitHub repo cache
        if is_github and project_path:
            cleanup_repo(project_path)


if __name__ == '__main__':
    main()
