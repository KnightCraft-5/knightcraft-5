# KnightCraft 5

packwiz ile yönetilen bir Minecraft Forge 1.20.1 mod paketi (189 mod).

Depoda mod listesi (packwiz metadatası), ayarlar, scriptler ve quest'ler tutuluyor; mod dosyaları (jar) burada değil. Modlar CurseForge kimliğiyle referans veriliyor ve kurulumda launcher tarafından indiriliyor. (CurseForge'da olmayan iki mod istisna; onlar `mods/` altında jar olarak duruyor.)

Pakete katkı vermek istiyorsan [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bak.

## Kurulum (oynamak için)

En son sürümü indir ve bir launcher'a aktar; modlar otomatik iner:

- CurseForge uygulaması: Create Custom Profile → Import → zip'i seç.
- Prism Launcher: Add Instance → Import → CurseForge zip'ini seç.

İndirme (her zaman en son sürüm):
https://github.com/KnightCraft-5/knightcraft-5/releases/latest/download/KnightCraft5.zip

## Sürüm çıkarma

`pack.toml` içindeki `version` satırını yükseltip push'la; CI paketi otomatik olarak Releases'e yayınlar. Yerelde denemek için: `packwiz curseforge export -o KnightCraft5.zip`.

Sürüm numarası: yalnızca ayar değişikliğinde son rakamı (5.0.1), mod değişikliğinde ortadakini (5.1.0), büyük değişiklikte ilkini (6.0.0) artır.
