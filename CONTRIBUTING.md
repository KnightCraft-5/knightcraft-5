# KnightCraft 5 geliştirme

Ayar, script ve quest düzenlemeleri için komut satırına ihtiyacın yok; hepsini GitHub Desktop üzerinden yaparsın. Mod ekleyip çıkarmayı ise packwiz ile lokalde hallediyoruz.

## Kurulum

Önce şu üç programı kur: [Prism Launcher](https://prismlauncher.org/), [Git](https://git-scm.com/downloads) ve [GitHub Desktop](https://desktop.github.com/).

1. Prism'de Minecraft 1.20.1 ve Forge 47.4.10 ile yeni bir instance oluştur. Bu aşamada çalıştırma.
2. Instance'ı seçip sağdaki Folder butonuna bas. Açılan klasör instance klasörüdür; içinde `instance.cfg`, `mmc-pack.json` ve boş bir `minecraft` klasörü bulunur. `instance.cfg` ve `mmc-pack.json` dosyalarını silme, Prism'in bunlara ihtiyacı var. Sadece içindeki boş `minecraft` klasörünü sil.
3. GitHub Desktop'ta `KnightCraft-5/knightcraft-5` deposunu klonla. Klonlama penceresindeki "Local path"i, sildiğin `minecraft` klasörünün yerine ayarla; yani yol `.../instances/<instance-adı>/minecraft` ile bitmeli. GitHub Desktop'un sona otomatik eklediği depo adını `minecraft` ile değiştir, klasörü kendisi oluşturur.
4. Modları indir: Windows'ta `scripts\refresh-mods.bat`, Mac veya Linux'ta `scripts/refresh-mods.sh` dosyasını çalıştır.

Bu kadar. Artık Prism'den başlatıp paketi oynayabilirsin.

## Çalışma akışı

Çalışmaya başlamadan önce GitHub Desktop'ta Pull yaparak herkesin son değişikliklerini al. Ayarları ya da scriptleri düzenle, oyunu yeniden başlatıp test et. KubeJS ve datapack değişikliklerinde oyunu kapatmana gerek yok; oyun içinde `/reload` (KubeJS scriptleri için `/kubejs reload`) yeterli. Sonuçtan memnunsan Commit ve Push yap.

İki küçük not: Pull'dan önce kendi değişikliğini kaydetmezsen GitHub Desktop izin vermez, ve aynı dosyayı iki kişi aynı anda düzenlerse çakışma çıkar. O yüzden sık commit yapın ve kimin neye baktığını aranızda konuşun.

Biri yeni bir mod eklediğinde, o modu kendi oyununa almak için Pull yapıp refresh-mods'u tekrar çalıştırman gerekir. Sadece config değiştiyse buna gerek yok, Pull yapman yeterli.

## Mod ekleme ve çıkarma

Modları packwiz ile lokalde yönetiyoruz. Eklemek için `packwiz curseforge add <curseforge-linki>`, çıkarmak için `packwiz remove <mod-adı>` çalıştır; sonra değişikliği commit'leyip push'la. Diğerleri Pull yapıp refresh-mods'u çalıştırınca mod onların da oyununa iner ya da oradan kalkar.

CurseForge'da olmayan modlar için: Modrinth'teyse `packwiz modrinth add <ad>`, doğrudan indirme linki varsa `packwiz url add <ad> <link>` kullan. İkisi de olmuyorsa (indirilemeyen ya da dağıtımı kapalı mod) jar'ı doğrudan pakete göm: `scripts/bundle-jar.sh <jar-yolu>` (Windows'ta `scripts\bundle-jar.bat`). Jar depoya girer, herkes Pull + refresh-mods ile alır.

Eklediğin ya da çıkardığın mod, yeni bir sürüm çıkana kadar oyunculara ulaşmaz.

## Sürüm çıkarma

`pack.toml` dosyasındaki `version` satırını yükselt, commit'le ve push'la; gerisini CI hallediyor. Hazır zip, Releases sekmesinde yayınlanır. Yeni sürüm herkese duyuru gönderdiği için gerçekten hazır olduğundan emin ol.
