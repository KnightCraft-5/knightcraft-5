# KnightCraft 5

packwiz ile yönetilen bir Minecraft Forge 1.20.1 mod paketi (189 mod).

Modların jar dosyaları depoda tutulmuyor; `mods` klasöründeki `.pw.toml` dosyaları her modu CurseForge'dan indirmek için gereken bilgiyi saklıyor. Depoda ayarlar, scriptler ve questler bulunuyor.

Pakete katkı vermek istiyorsan [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına göz at.

## Sürüm çıkarma

`pack.toml` içindeki `version` satırını yükseltip push'lamak yeterli; CI yeni sürümü otomatik olarak Releases'e yayınlar (aynı sürüm zaten yayınlandıysa atlar).

Her zaman en son sürümü veren sabit indirme linki:
https://github.com/KnightCraft-5/knightcraft-5/releases/latest/download/KnightCraft5.zip

Sürüm numarasını şöyle belirle: yalnızca ayar değişikliğinde son rakamı (5.0.1), mod değişikliğinde ortadakini (5.1.0), büyük elden geçirmede ilkini (6.0.0) artır.
