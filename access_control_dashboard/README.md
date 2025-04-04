# Erişim Kontrol Paneli

Bu proje, erişim kontrol sistemlerinden gelen verileri görselleştiren bir dashboard uygulamasıdır.

## Proje Yapısı

```
access_control_dashboard/
│── backend/                 # Python backend (Flask API)
│   ├── app.py              # Ana Flask API
│   ├── database.py         # MSSQL bağlantısı
│   ├── config.py           # Veritabanı ayarları
│── frontend/               # Dashboard (Dash + Plotly)
│   ├── dashboard.py        # Ana Dash uygulaması
│── requirements.txt        # Gerekli Python kütüphaneleri
│── run_backend.sh         # Backend başlatma scripti
│── run_frontend.sh        # Frontend başlatma scripti
│── README.md
```

## Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

2. Veritabanı bağlantı ayarlarını yapılandırın:
- `backend/config.py` dosyasını düzenleyin
- Veya `.env` dosyası oluşturup aşağıdaki değişkenleri tanımlayın:
```
DB_SERVER=your_server
DB_DATABASE=your_database
DB_USERNAME=your_username
DB_PASSWORD=your_password
```

## Çalıştırma

1. Backend'i başlatın:
```bash
./run_backend.sh
```

2. Frontend'i başlatın:
```bash
./run_frontend.sh
```

3. Tarayıcınızda şu adresi açın:
```
http://localhost:8050
```

## Özellikler

- Kapı bazlı erişim istatistikleri grafiği
- Son erişim logları tablosu
- 5 dakikada bir otomatik veri güncelleme
- Responsive tasarım

## API Endpoints

- `GET /api/access-logs`: Son erişim loglarını getirir
- `GET /api/door-statistics`: Kapı bazlı erişim istatistiklerini getirir 