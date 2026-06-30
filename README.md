# KnightCraft 5

[packwiz](https://packwiz.infra.link/) ile yönetilen bir Minecraft **Forge 1.20.1**
mod paketi (189 mod).

Bu depo paketin **ana kaynağıdır**: mod sürümleri, ayarlar (config), scriptler ve
özel ana menü burada tutulur. Mod dosyalarının (jar) kendisi burada saklanmaz —
`mods/*.pw.toml` içinde CurseForge proje/dosya kimliğiyle işaret edilir ve kurulum
sırasında indirilir.

## Klasör yapısı

| Yol | Açıklama |
|------|------|
| `pack.toml` / `index.toml` | packwiz paket bilgisi + dosya dizini |
| `mods/*.pw.toml` | her mod için bir dosya — CurseForge kimliği + hash |
| `*.pw.toml` (kök) | shader paketleri (Complementary, Sildur's) |
| `config/`, `defaultconfigs/`, `kubejs/` | mod ayarları ve scriptler |
| `packmenu/`, `resourcepacks/` | özel ana menü ve paket içi doku paketleri |
| `serverconfig/` | sunucu tarafı ayarlar (depoda tutulur, dışa aktarmaya dahil edilmez) |

## Pakete katkıda bulunmak

Paketi geliştiriyorsan kurulum ve günlük akış için **[CONTRIBUTING.md](CONTRIBUTING.md)**
dosyasına bak (terminal gerekmez — GitHub Desktop + Prism Launcher).

## Dağıtılabilir paket oluşturma

```bash
packwiz curseforge export -o KnightCraft5.zip
```

`KnightCraft5.zip` dosyasını CurseForge uygulamasına aktar
(Create Custom Profile → Import).

## Bakımcı (maintainer) komutları

```bash
packwiz curseforge add <slug>     # mod ekle
packwiz update --all              # her şeyi en güncele yükselt
git add -A && git commit -m "..." # değişikliği kaydet
```
