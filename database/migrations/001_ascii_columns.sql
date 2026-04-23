-- DB Migration: Turkce karakter kolonlari ASCII'ye donusturuldu
-- Tarih: 2026-04-23

ALTER TABLE notlar RENAME COLUMN "icerik" TO icerik;
ALTER TABLE notlar RENAME COLUMN "tamamlandi" TO tamamlandi;
ALTER TABLE notlar RENAME COLUMN "hatirlatma" TO hatirlatma;
ALTER TABLE konusmalar RENAME COLUMN "icerik" TO icerik;
ALTER TABLE bilgiler RENAME COLUMN "yanit" TO yanit;
ALTER TABLE gecmis_notlar RENAME COLUMN "icerik" TO icerik;
ALTER TABLE gecmis_notlar RENAME COLUMN "olusturma" TO olusturma;
ALTER TABLE gecmis_notlar RENAME COLUMN "hatirlatma" TO hatirlatma;
ALTER TABLE rezervasyonlar RENAME COLUMN "tur" TO tur;
ALTER TABLE rezervasyonlar RENAME COLUMN "sehir" TO sehir;
ALTER TABLE rezervasyonlar RENAME COLUMN "giris_tarihi" TO giris_tarihi;
ALTER TABLE rezervasyonlar RENAME COLUMN "cikis_tarihi" TO cikis_tarihi;
ALTER TABLE rezervasyonlar RENAME COLUMN "kisi" TO kisi;
