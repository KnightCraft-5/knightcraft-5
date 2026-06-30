# KnightCraft 5 — Geliştirme

Terminal yok. Ayarları düzenlersin, GitHub Desktop'ta kaydedersin. Mod listesini bakımcı yönetir.

## Kurulum (bir kez)

Şunları kur: [Prism Launcher](https://prismlauncher.org/), [Git](https://git-scm.com/downloads), [GitHub Desktop](https://desktop.github.com/).

1. Prism'de yeni instance: Minecraft 1.20.1 + Forge 47.4.10. Bir kez çalıştır, kapat.
2. Prism'de instance → **Folder** → `minecraft` klasörünü aç, içini boşalt.
3. GitHub Desktop → **Clone** → `KnightCraft-5/knightcraft-5`, hedef klasör olarak o `minecraft` klasörünü seç.
4. Modları indir: Windows'ta `scripts\refresh-mods.bat`, Mac/Linux'ta `scripts/refresh-mods.sh`.

Prism'den başlat — paketi oynuyorsun.

## Günlük iş

GitHub Desktop'ta: **Pull → düzenle → Commit → Push**

- Başlamadan **Pull** at (herkesin son halini al).
- Ayarı değiştir, oyunu yeniden başlat ve test et. KubeJS/datapack için yeniden başlatmadan `/reload` (scriptler için `/kubejs reload`).
- İyiyse **Commit** + **Push**.

Pull'dan önce kendi değişikliğini kaydet, yoksa GitHub Desktop izin vermez. Aynı dosyayı aynı anda iki kişi düzenlerse çakışır — sık commit atın, kimin neye baktığını konuşun.

## Mod ekleme/çıkarma

Bakımcıya söyle. Liste değişince sen sadece **Pull** at ve **refresh-mods**'u tekrar çalıştır. Başka zaman gerekmez.

## Sürüm çıkarma (bakımcı)

`pack.toml` içindeki `version` satırını yükselt, commit'le, push'la. CI otomatik yayınlar. Zip **Releases**'te; sabit link `…/releases/latest/download/KnightCraft5.zip`.
