# KnightCraft 5 geliştirme

Paket packwiz ile yönetiliyor. Depoda mod listesi (packwiz metadatası), ayarlar, scriptler ve quest'ler var; mod dosyalarının (jar) kendisi tutulmuyor. Oynamak ve test etmek için paketi CurseForge zip'i olarak dışa aktarıp bir launcher'a aktarıyoruz; launcher bütün modları CurseForge'dan indiriyor. Böylece kimse jar taşımıyor.

## Ayar, script ve quest düzenleme

Bunun için packwiz gerekmez. Depoyu klonla, `config`, `kubejs`, `defaultconfigs` ya da `serverconfig` altındaki dosyaları düzenle, commit'leyip push'la. Değişikliği oyunda görmek için aşağıdaki "Paketi oynama/test etme" adımını izle.

## Mod ekleme ve çıkarma

Bunun için [packwiz](https://packwiz.infra.link/) kur (Go ile: `go install github.com/packwiz/packwiz@latest`).

- Eklemek: `packwiz curseforge add <curseforge-linki-veya-adı>`
- Çıkarmak: `packwiz remove <mod-adı>`
- CurseForge'da yoksa: Modrinth'teyse `packwiz modrinth add <ad>`, doğrudan indirme linki varsa `packwiz url add <ad> <link>`. Hiçbiri olmuyorsa jar'ı doğrudan göm: `scripts/bundle-jar.sh <jar-yolu>` (Windows'ta `scripts\bundle-jar.bat`).

Ardından commit'leyip push'la.

## Paketi oynama/test etme

Paketi tek komutla CurseForge zip'i olarak dışa aktar:

    packwiz curseforge export -o KnightCraft5.zip

Bu zip'i bir launcher'a aktar; modların hepsi otomatik iner:

- CurseForge uygulaması: Create Custom Profile → Import → zip'i seç. En sorunsuz yol.
- Prism Launcher: Add Instance → Import → CurseForge zip'ini seç.

Yeni sürüm çıkarmak (oyunculara göndermek) için `pack.toml` içindeki `version` satırını yükselt, commit'le ve push'la; CI paketi otomatik olarak Releases'e koyar.

## Not: Linux + Prism'de Forge kurulum hatası

Prism'de Forge kurarken "Processor failed, invalid outputs" hatası alırsan instance'ın Java'sını gamma yerine Temurin 17'ye çevir (Settings → Java). Prism'in indirdiği gamma runtime'ı bu Forge sürümünün kurulumunu bozuyor. CurseForge uygulamasında bu sorun yok.
