# KnightCraft 5 geliştirme

Paketi geliştirmek için komut satırına ihtiyacın yok. Ayarları düzenler, değişiklikleri GitHub Desktop üzerinden kaydedersin. Mod listesini bakımcı yönetir.

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

## Mod ekleme

Eklemek istediğin modun CurseForge linkini kopyala. [Add a mod](https://github.com/KnightCraft-5/knightcraft-5/actions/workflows/add-mod.yml) sayfasına gidip Run workflow'a bas ve linki yapıştır. İşlem bitince GitHub Desktop'ta Pull yap, ardından refresh-mods'u tekrar çalıştır; mod inip oyuna gelir.

Mod silmek ya da sürüm düşürmek istersen bakımcıya söyle. Eklediğin mod, bakımcı yeni bir sürüm çıkarana kadar oyunculara ulaşmaz.

## Sürüm çıkarma

Bu kısım bakımcı içindir. `pack.toml` dosyasındaki `version` satırını yükselt, commit'le ve push'la; gerisini CI hallediyor. Hazır zip, Releases sekmesinde yayınlanır.
