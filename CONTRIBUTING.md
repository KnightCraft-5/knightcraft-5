# KnightCraft 5 Geliştirme Rehberi

Paketi **git** (geçmiş + ortak çalışma) ve **packwiz** (modlar) ile geliştiriyoruz.
Terminal kullanman ya da packwiz öğrenmen gerekmiyor — sadece ayarları/scriptleri
düzenleyip kolay bir uygulamada Commit/Push'a tıklıyorsun. Mod listesini tek kişi
(bakımcı) yönetir.

---

## ⚡ Sadece config güncellemesi (en sık yapılan iş)

Kurulumu bir kez yaptıktan sonra, ayar/script/quest değişiklikleri için günlük iş
sadece bu — **terminal yok, mod indirmek yok:**

```
GitHub Desktop: Pull  →  oyunu yeniden başlat  →  düzenle & test et  →  Commit  →  Push
```

- **Pull** = herkesin son ayarlarını al. Değişiklikleri görmek için oyunu **kapatıp
  yeniden aç** (Minecraft ayarları sadece açılışta okur).
- **Pull'dan önce** kendi değişikliğini Commit'le ya da geri al, yoksa GitHub Desktop
  pull'a izin vermez.
- Aynı dosyayı aynı anda iki kişi düzenlerse çakışma olabilir — **sık pull at, küçük
  commit'le** ve kimin neye dokunduğunu kabaca konuşun (örn. biri questler, biri loot).
- `scripts/refresh-mods` **sadece mod listesi değişince** gerekir (nadiren). Sırf
  config işi için ona dokunmana gerek yok.

> Kurulumu hiç yapmadıysan önce aşağıdaki **Tek seferlik kurulum**'u tamamla.

---

## Tek seferlik kurulum (~15 dk)

Üç ücretsiz program lazım:

1. **[Prism Launcher](https://prismlauncher.org/)** — paketi çalıştırır.
2. **[Git](https://git-scm.com/downloads)** — sürüm kontrol motoru.
3. **[GitHub Desktop](https://desktop.github.com/)** — terminalsiz, butonlu git uygulaması.

### Adımlar

1. **Prism instance'ını oluştur**
   Prism → *Add Instance* → adını `KnightCraft 5` koy → **Minecraft 1.20.1** ve
   **Forge 47.4.10** seç → Create. Bir kez çalıştır ki kurulumu bitsin, sonra kapat.

2. **Instance'ın oyun klasörünü bul**
   Prism'de instance'ı seç → *Folder* butonu → `minecraft` (veya `.minecraft`)
   klasörünü aç. **İçindeki her şeyi sil** (sadece boş varsayılan dosyalar).

3. **Depoyu o klasörün içine klonla**
   GitHub Desktop'ta: *File → Clone repository →* `KnightCraft-5/knightcraft-5`.
   **Local path** olarak 2. adımdaki `minecraft` klasörünü seç.
   > Artık paket kaynağı, Minecraft'ın çalıştığı klasörle aynı. Buradaki bir ayarı
   > düzenlemek = paketi düzenlemek.

4. **Modları indir**
   O klasörde işletim sistemine göre yardımcı dosyayı çalıştır:
   - **Windows:** `scripts\refresh-mods.bat` dosyasına çift tıkla
   - **macOS/Linux:** `scripts/refresh-mods.sh` çalıştır

   ~189 mod jar'ını indirir. Instance'ı başlat — paketi oynuyorsun.

---

## Günlük akış (terminal yok)

```
GitHub Desktop:  Fetch/Pull   →   oyunda düzenle & test et   →   Commit   →   Push
```

1. **Önce Pull** (GitHub Desktop, üst bar) — herkesin en son işini al.
2. Ayarları / KubeJS scriptlerini / questleri / loot'u düzenle — oyun içinden ya da
   doğrudan dosyalardan.
3. GitHub Desktop tam olarak neyin değiştiğini gösterir. Kısa bir özet yaz
   (örn. *"şovalye zırhı dayanıklılığı artırıldı"*) → **Commit** → **Push**.

İşin tamamı bu. Küçük küçük ve sık commit at; hazır olunca push'la.

> **İpucu:** Pull'dan önce değişikliklerini commit'le ya da geri al ki git temiz
> birleştirebilsin.
>
> **İpucu:** Bazı modlar her açılışta kendi ayar dosyasını yeniden yazar, bu yüzden
> GitHub Desktop'ta dokunmadığın dosyalar değişmiş görünebilir. Sadece bilerek
> değiştirdiğin dosyaları işaretleyip commit at, gerisinin işaretini kaldır.

---

## Mod listesini değiştirmek (sadece bakımcı)

Mod ekleme/çıkarma/güncelleme packwiz verisini düzenlemek demek — bunu bakımcı yapar.
Eklenmesini istediğin modu ona söyle. Bakımcı şunları çalıştırır:

```bash
packwiz curseforge add <mod>      # ekle
packwiz update --all              # hepsini güncelle
git add -A && git commit -m "..." && git push
```

Mod listesi değişince herkes: GitHub Desktop'ta **Pull**, sonra yeni jar'ları almak
için **refresh-mods** scriptini tekrar çalıştırır.

---

## Oynanabilir sürüm paylaşmak (test/oyuncular için)

Bakımcı, CurseForge uygulamasına aktarılabilen bir zip dışa aktarır:

```bash
packwiz curseforge export -o KnightCraft5.zip
```
