import os
import shutil
import hashlib
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import pyfiglet
from termcolor import colored
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
import click

console = Console()

CATEGORIES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff'],
    'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
    'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
    'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods', '.numbers'],
    'Presentations': ['.ppt', '.pptx', '.odp', '.key'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
    'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go'],
    'Executables': ['.exe', '.msi', '.deb', '.rpm', '.dmg', '.app'],
    'Others': []
}

class FileOrganizer:
    def __init__(self, source_dir, output_dir=None):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir) if output_dir else self.source_dir / "Organized"
        self.duplicates = defaultdict(list)
        self.processed_files = 0
        self.total_files = 0

    def get_file_hash(self, filepath):
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return None

    def get_category(self, file_ext):
        for category, extensions in CATEGORIES.items():
            if file_ext.lower() in extensions:
                return category
        return 'Others'

    def sanitize_filename(self, filename):
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        return filename

    def find_duplicates(self):
        console.print("[yellow]🔍 Recherche de doublons...[/yellow]")
        file_hashes = defaultdict(list)
        
        for filepath in self.source_dir.rglob('*'):
            if filepath.is_file():
                file_hash = self.get_file_hash(filepath)
                if file_hash:
                    file_hashes[file_hash].append(filepath)
        
        self.duplicates = {h: files for h, files in file_hashes.items() if len(files) > 1}
        return len(self.duplicates)

    def organize_by_type(self):
        console.print("[green]📁 Organisation par type...[/green]")
        
        files = list(self.source_dir.rglob('*'))
        self.total_files = len([f for f in files if f.is_file()])
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Organisation...", total=self.total_files)
            
            for filepath in files:
                if filepath.is_file():
                    category = self.get_category(filepath.suffix)
                    category_dir = self.output_dir / category
                    category_dir.mkdir(parents=True, exist_ok=True)
                    
                    dest_path = category_dir / filepath.name
                    counter = 1
                    while dest_path.exists():
                        name = filepath.stem
                        ext = filepath.suffix
                        dest_path = category_dir / f"{name}_{counter}{ext}"
                        counter += 1
                    
                    try:
                        shutil.move(str(filepath), str(dest_path))
                        self.processed_files += 1
                    except:
                        pass
                    
                    progress.update(task, advance=1)

    def organize_by_date(self):
        console.print("[blue]📅 Organisation par date...[/blue]")
        
        files = list(self.source_dir.rglob('*'))
        self.total_files = len([f for f in files if f.is_file()])
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Organisation...", total=self.total_files)
            
            for filepath in files:
                if filepath.is_file():
                    try:
                        mod_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                        year_month = mod_time.strftime("%Y-%m")
                        date_dir = self.output_dir / year_month
                        date_dir.mkdir(parents=True, exist_ok=True)
                        
                        dest_path = date_dir / filepath.name
                        counter = 1
                        while dest_path.exists():
                            name = filepath.stem
                            ext = filepath.suffix
                            dest_path = date_dir / f"{name}_{counter}{ext}"
                            counter += 1
                        
                        shutil.move(str(filepath), str(dest_path))
                        self.processed_files += 1
                    except:
                        pass
                    
                    progress.update(task, advance=1)

    def bulk_rename(self, pattern, replacement):
        console.print("[magenta]✏️  Renommage en masse...[/magenta]")
        renamed = 0
        
        for filepath in self.source_dir.rglob('*'):
            if filepath.is_file():
                old_name = filepath.name
                new_name = re.sub(pattern, replacement, old_name)
                new_name = self.sanitize_filename(new_name)
                
                if new_name != old_name:
                    new_path = filepath.parent / new_name
                    counter = 1
                    while new_path.exists():
                        name = Path(new_name).stem
                        ext = Path(new_name).suffix
                        new_path = filepath.parent / f"{name}_{counter}{ext}"
                        counter += 1
                    
                    try:
                        filepath.rename(new_path)
                        renamed += 1
                    except:
                        pass
        
        return renamed

def print_banner():
    ascii_art = pyfiglet.figlet_format("FILE ORGANIZER", font='slant')
    console.print(colored(ascii_art, 'cyan'))
    console.print(colored("=" * 70, 'yellow'))
    console.print(colored("🚀 Smart File Organizer - Votre assistant de fichiers 📁", 'green'))
    console.print(colored("=" * 70, 'yellow'))

def display_duplicates(duplicates):
    if not duplicates:
        console.print("[green]✅ Aucun doublon trouvé![/green]")
        return
    
    table = Table(title="🔍 Doublons détectés")
    table.add_column("Fichier", style="cyan")
    table.add_column("Taille", style="yellow")
    table.add_column("Emplacements", style="white")
    
    for file_hash, files in list(duplicates.items())[:10]:
        first_file = files[0]
        size = first_file.stat().st_size
        size_str = f"{size:,} bytes"
        locations = "\n".join([str(f.parent) for f in files])
        table.add_row(first_file.name, size_str, locations)
    
    console.print(table)
    console.print(f"[red]📊 Total: {len(duplicates)} groupes de doublons[/red]")

def main_menu():
    print_banner()
    
    while True:
        console.print("\n[bold cyan]🎯 MENU PRINCIPAL[/bold cyan]")
        console.print("[cyan]1.[/cyan] Organiser par type de fichier")
        console.print("[cyan]2.[/cyan] Organiser par date")
        console.print("[cyan]3.[/cyan] Détecter les doublons")
        console.print("[cyan]4.[/cyan] Renommage en masse")
        console.print("[cyan]5.[/cyan] Nettoyer les doublons")
        console.print("[cyan]0.[/cyan] Quitter")
        
        choice = input(colored("\nVotre choix: ", 'green')).strip()
        
        if choice == '1':
            source = input(colored("📂 Dossier source: ", 'yellow')).strip()
            if not os.path.exists(source):
                console.print("[red]❌ Dossier inexistant[/red]")
                continue
                
            output = input(colored("📁 Dossier de sortie (optionnel): ", 'yellow')).strip()
            organizer = FileOrganizer(source, output if output else None)
            organizer.organize_by_type()
            console.print(f"[green]✅ {organizer.processed_files} fichiers organisés![/green]")
        
        elif choice == '2':
            source = input(colored("📂 Dossier source: ", 'yellow')).strip()
            if not os.path.exists(source):
                console.print("[red]❌ Dossier inexistant[/red]")
                continue
                
            output = input(colored("📁 Dossier de sortie (optionnel): ", 'yellow')).strip()
            organizer = FileOrganizer(source, output if output else None)
            organizer.organize_by_date()
            console.print(f"[green]✅ {organizer.processed_files} fichiers organisés![/green]")
        
        elif choice == '3':
            source = input(colored("📂 Dossier à analyser: ", 'yellow')).strip()
            if not os.path.exists(source):
                console.print("[red]❌ Dossier inexistant[/red]")
                continue
                
            organizer = FileOrganizer(source)
            duplicates_count = organizer.find_duplicates()
            display_duplicates(organizer.duplicates)
        
        elif choice == '4':
            source = input(colored("📂 Dossier source: ", 'yellow')).strip()
            if not os.path.exists(source):
                console.print("[red]❌ Dossier inexistant[/red]")
                continue
                
            pattern = input(colored("🔍 Pattern à remplacer (regex): ", 'yellow')).strip()
            replacement = input(colored("✏️  Remplacement: ", 'yellow')).strip()
            
            organizer = FileOrganizer(source)
            renamed = organizer.bulk_rename(pattern, replacement)
            console.print(f"[green]✅ {renamed} fichiers renommés![/green]")
        
        elif choice == '5':
            source = input(colored("📂 Dossier à nettoyer: ", 'yellow')).strip()
            if not os.path.exists(source):
                console.print("[red]❌ Dossier inexistant[/red]")
                continue
                
            organizer = FileOrganizer(source)
            duplicates_count = organizer.find_duplicates()
            
            if duplicates_count == 0:
                console.print("[green]✅ Aucun doublon à supprimer![/green]")
                continue
            
            display_duplicates(organizer.duplicates)
            confirm = input(colored("⚠️  Supprimer les doublons? (y/N): ", 'red')).strip().lower()
            
            if confirm == 'y':
                deleted = 0
                for files in organizer.duplicates.values():
                    for file_to_delete in files[1:]:
                        try:
                            file_to_delete.unlink()
                            deleted += 1
                        except:
                            pass
                console.print(f"[green]✅ {deleted} doublons supprimés![/green]")
        
        elif choice == '0':
            console.print("[green]👋 Au revoir![/green]")
            break
        
        else:
            console.print("[red]❌ Choix invalide[/red]")

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Arrêt par l'utilisateur[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Erreur: {e}[/red]")

# By DlDml , 2025. All rights reserved.
