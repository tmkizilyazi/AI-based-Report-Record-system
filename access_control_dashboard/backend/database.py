import pyodbc
import requests
from config import (
    DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD,
    GEMINI_API_KEY, GEMINI_API_URL, DB_ENCRYPTION_KEY
)

def test_db_connection():
    """Veritabanı bağlantısını test eder"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        # Tüm tabloları listele
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()
        
        # Sonuçları formatla
        table_content = "\nVeritabanındaki Tablolar:\n"
        table_content += "-" * 50 + "\n"
        
        for table in tables:
            table_name = table[0]
            # Her tablonun ilk 10 kaydını getir
            cursor.execute(f"SELECT TOP 10 * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Sütun isimlerini al
            columns = [column[0] for column in cursor.description]
            
            table_content += f"\nTablo: {table_name}\n"
            table_content += "-" * 50 + "\n"
            table_content += " | ".join(columns) + "\n"
            table_content += "-" * 50 + "\n"
            
            for row in rows:
                table_content += " | ".join(str(cell) for cell in row) + "\n"
            table_content += "\n"
        
        cursor.close()
        conn.close()
        return f"Bağlantı başarılı! SQL Server Versiyonu: {version}\n{table_content}"
    except Exception as e:
        return f"Bağlantı hatası: {str(e)}"

def get_db_connection():
    """MSSQL veritabanına bağlantı oluşturur"""
    try:
        conn_str = (
            f'DRIVER={{SQL Server}};'
            f'SERVER={DB_SERVER};'
            f'DATABASE={DB_DATABASE};'
            f'UID={DB_USERNAME};'
            f'PWD={DB_PASSWORD};'
            'MultipleActiveResultSets=true;'
            'TrustServerCertificate=True;'
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Veritabanı bağlantı hatası: {str(e)}")
        # Gerçek ortamda hata fırlatmak yerine boş sonuç döndürüyoruz
        # Bu sayede frontend'de hata olmadan boş grafikler gösterilebilir
        raise Exception(f"Veritabanı bağlantı hatası: {str(e)}")

def execute_query(query, params=None):
    """Veritabanı sorgusu çalıştırır ve sonuçları döndürür"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Sorgu hatası: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_access_logs():
    """Erişim loglarını getirir"""
    try:
        query = """
        SELECT TOP 100 
            AccessTime,
            UserID,
            DoorID,
            AccessType,
            CardNumber,
            UserName
        FROM AccessLogs
        ORDER BY AccessTime DESC
        """
        results = execute_query(query)
        return [{
            'access_time': str(row[0]),
            'user_id': row[1],
            'door_id': row[2],
            'access_type': row[3],
            'card_number': row[4],
            'user_name': row[5]
        } for row in results]
    except Exception as e:
        print(f"Erişim logları alınamadı: {str(e)}")
        return []

def get_door_statistics():
    """Kapı istatistiklerini getirir"""
    try:
        query = """
        SELECT 
            DoorID,
            DoorName,
            COUNT(*) as AccessCount,
            COUNT(CASE WHEN AccessType = 'success' THEN 1 END) as SuccessCount,
            COUNT(CASE WHEN AccessType = 'failed' THEN 1 END) as FailedCount
        FROM AccessLogs
        GROUP BY DoorID, DoorName
        ORDER BY AccessCount DESC
        """
        results = execute_query(query)
        return [{
            'door_id': row[0],
            'door_name': row[1],
            'access_count': row[2],
            'success_count': row[3],
            'failed_count': row[4]
        } for row in results]
    except Exception as e:
        print(f"Kapı istatistikleri alınamadı: {str(e)}")
        return []

def get_user_statistics():
    """Kullanıcı istatistiklerini getirir"""
    try:
        query = """
        SELECT 
            UserID,
            UserName,
            COUNT(*) as AccessCount,
            COUNT(CASE WHEN AccessType = 'success' THEN 1 END) as SuccessCount,
            COUNT(CASE WHEN AccessType = 'failed' THEN 1 END) as FailedCount
        FROM AccessLogs
        GROUP BY UserID, UserName
        ORDER BY AccessCount DESC
        """
        results = execute_query(query)
        return [{
            'user_id': row[0],
            'user_name': row[1],
            'access_count': row[2],
            'success_count': row[3],
            'failed_count': row[4]
        } for row in results]
    except Exception as e:
        print(f"Kullanıcı istatistikleri alınamadı: {str(e)}")
        return []

def get_hourly_statistics():
    """Saatlik erişim istatistiklerini getirir"""
    try:
        query = """
        SELECT 
            DATEPART(HOUR, AccessTime) as Hour,
            COUNT(*) as AccessCount,
            COUNT(CASE WHEN AccessType = 'success' THEN 1 END) as SuccessCount,
            COUNT(CASE WHEN AccessType = 'failed' THEN 1 END) as FailedCount
        FROM AccessLogs
        GROUP BY DATEPART(HOUR, AccessTime)
        ORDER BY Hour
        """
        results = execute_query(query)
        return [{
            'hour': row[0],
            'access_count': row[1],
            'success_count': row[2],
            'failed_count': row[3]
        } for row in results]
    except Exception as e:
        print(f"Saatlik istatistikler alınamadı: {str(e)}")
        return []

def get_gemini_headers():
    """Gemini API için gerekli header'ları oluşturur"""
    return {
        'Content-Type': 'application/json',
        'x-goog-api-key': GEMINI_API_KEY
    }

def analyze_with_gemini(prompt, data=None, sql_query=None):
    """Gemini AI ile veri analizi yapar veya SQL sorgusu çalıştırır"""
    endpoint = f'{GEMINI_API_URL}/gemini-pro:generateContent'
    
    full_prompt = prompt
    
    # Eğer veri sağlanmışsa, prompt'a ekle
    if data is not None:
        data_str = str(data)
        full_prompt = f"""
        {prompt}
        
        Veri:
        {data_str}
        
        Lütfen bu veriyi analiz et ve önemli noktaları özetle.
        """
    
    # Eğer SQL sorgusu sağlanmışsa, prompt'a ekle
    if sql_query is not None:
        full_prompt = f"""
        {prompt}
        
        Aşağıdaki SQL sorgusunu kullanıcı dostu bir şekilde analiz et ve açıkla:
        ```sql
        {sql_query}
        ```
        
        Sorgu ne tür veriler getiriyor? Hangi tablolar kullanılıyor? Ne tür filtreleme yapılıyor?
        En önemli kısımlarını açıkla ve varsa, bu sorguda dikkat edilmesi gereken şeyleri belirt.
        """
    
    payload = {
        "contents": [{
            "parts": [{
                "text": full_prompt
            }]
        }]
    }
    
    try:
        response = requests.post(endpoint, headers=get_gemini_headers(), json=payload)
        
        if response.status_code == 200:
            response_data = response.json()
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                if 'content' in response_data['candidates'][0]:
                    if 'parts' in response_data['candidates'][0]['content']:
                        if len(response_data['candidates'][0]['content']['parts']) > 0:
                            return response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Varsayılan yanıt formatı için
            return response_data
        else:
            error_message = f'Gemini API Hatası: {response.status_code}'
            print(error_message)
            return {"error": error_message}
    except Exception as e:
        error_message = f'Gemini API İstek Hatası: {str(e)}'
        print(error_message)
        return {"error": error_message}

def analyze_access_logs():
    """Erişim loglarını analiz eder"""
    logs = get_access_logs()
    prompt = "Son erişim loglarını analiz et ve önemli noktaları özetle."
    return analyze_with_gemini(prompt, logs)

def analyze_door_statistics():
    """Kapı istatistiklerini analiz eder"""
    stats = get_door_statistics()
    prompt = "Kapı erişim istatistiklerini analiz et ve önemli noktaları özetle."
    return analyze_with_gemini(prompt, stats)

def analyze_user_statistics():
    """Kullanıcı istatistiklerini analiz eder"""
    stats = get_user_statistics()
    prompt = "Kullanıcı erişim istatistiklerini analiz et ve önemli noktaları özetle."
    return analyze_with_gemini(prompt, stats)

def analyze_hourly_statistics():
    """Saatlik istatistikleri analiz eder"""
    stats = get_hourly_statistics()
    prompt = "Saatlik erişim istatistiklerini analiz et ve önemli noktaları özetle."
    return analyze_with_gemini(prompt, stats)

def get_database_schema():
    """Veritabanı şemasını ve ilişkileri getirir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tabloları listele
        cursor.execute("""
            SELECT 
                t.TABLE_NAME,
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.IS_NULLABLE,
                c.COLUMN_DEFAULT,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as IS_PRIMARY_KEY
            FROM INFORMATION_SCHEMA.TABLES t
            JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
            LEFT JOIN (
                SELECT ku.COLUMN_NAME, ku.TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS ku
                    ON tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                    AND tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
            ) pk ON c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
        """)
        
        tables = {}
        for row in cursor.fetchall():
            table_name = row[0]
            if table_name not in tables:
                tables[table_name] = {'columns': []}
            tables[table_name]['columns'].append({
                'name': row[1],
                'data_type': row[2],
                'is_nullable': row[3],
                'default_value': row[4],
                'is_primary_key': bool(row[5])
            })
        
        # Foreign key ilişkilerini getir
        cursor.execute("""
            SELECT 
                fk.TABLE_NAME as FK_TABLE,
                fk.COLUMN_NAME as FK_COLUMN,
                pk.TABLE_NAME as PK_TABLE,
                pk.COLUMN_NAME as PK_COLUMN
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk
                ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk
                ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
            ORDER BY fk.TABLE_NAME, fk.COLUMN_NAME
        """)
        
        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                'from_table': row[0],
                'from_column': row[1],
                'to_table': row[2],
                'to_column': row[3]
            })
        
        # Eğer ilişkiler bulunamazsa, ID sütunları arasında olası ilişkileri tahmin et
        if not relationships:
            # Tüm tabloları ve primary key'leri depola
            primary_keys = {}
            possible_foreign_keys = {}
            
            for table_name, table_data in tables.items():
                # Primary key'leri bul
                pk_columns = []
                for column in table_data['columns']:
                    if column['is_primary_key']:
                        pk_columns.append(column['name'])
                        primary_keys[table_name] = pk_columns
                
                # Olası foreign key'leri bul (id ile biten veya başlayan kolonlar)
                for column in table_data['columns']:
                    col_name = column['name'].lower()
                    if not column['is_primary_key'] and ('id' in col_name or col_name.endswith('_key') or col_name.endswith('_no')):
                        possible_foreign_keys.setdefault(table_name, []).append(column['name'])
            
            # Primary key'ler ve olası foreign key'ler arasında bağlantı kur
            for table_name, fk_columns in possible_foreign_keys.items():
                for fk_column in fk_columns:
                    fk_column_lower = fk_column.lower().replace('_id', '').replace('id_', '')
                    
                    for pk_table, pk_columns in primary_keys.items():
                        if pk_table != table_name:  # Kendi kendine referans vermesin
                            # İsim benzerliği kontrolü
                            if (fk_column_lower in pk_table.lower() or 
                                pk_table.lower().replace('_', '') in fk_column_lower or
                                pk_table.lower() == fk_column_lower):
                                
                                for pk_column in pk_columns:
                                    relationships.append({
                                        'from_table': table_name,
                                        'from_column': fk_column,
                                        'to_table': pk_table,
                                        'to_column': pk_column
                                    })
                                    break
        
        cursor.close()
        conn.close()
        
        # Test verileri yoksa örnek veriler ekle
        if not tables:
            # Örnek tablolar - basit erişim kontrol sistemi
            tables = {
                "Users": {
                    "columns": [
                        {"name": "UserID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": True},
                        {"name": "UserName", "data_type": "varchar", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "Email", "data_type": "varchar", "is_nullable": "YES", "default_value": None, "is_primary_key": False},
                        {"name": "DepartmentID", "data_type": "int", "is_nullable": "YES", "default_value": None, "is_primary_key": False},
                        {"name": "CardNumber", "data_type": "varchar", "is_nullable": "YES", "default_value": None, "is_primary_key": False}
                    ]
                },
                "Departments": {
                    "columns": [
                        {"name": "DepartmentID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": True},
                        {"name": "DepartmentName", "data_type": "varchar", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "Location", "data_type": "varchar", "is_nullable": "YES", "default_value": None, "is_primary_key": False}
                    ]
                },
                "Doors": {
                    "columns": [
                        {"name": "DoorID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": True},
                        {"name": "DoorName", "data_type": "varchar", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "DoorLocation", "data_type": "varchar", "is_nullable": "YES", "default_value": None, "is_primary_key": False},
                        {"name": "IsActive", "data_type": "bit", "is_nullable": "NO", "default_value": "1", "is_primary_key": False}
                    ]
                },
                "AccessLogs": {
                    "columns": [
                        {"name": "LogID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": True},
                        {"name": "UserID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "DoorID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "AccessTime", "data_type": "datetime", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "AccessType", "data_type": "varchar", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "DeviceID", "data_type": "int", "is_nullable": "YES", "default_value": None, "is_primary_key": False}
                    ]
                },
                "Permissions": {
                    "columns": [
                        {"name": "PermissionID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": True},
                        {"name": "UserID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "DoorID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "StartTime", "data_type": "time", "is_nullable": "YES", "default_value": None, "is_primary_key": False},
                        {"name": "EndTime", "data_type": "time", "is_nullable": "YES", "default_value": None, "is_primary_key": False},
                        {"name": "IsActive", "data_type": "bit", "is_nullable": "NO", "default_value": "1", "is_primary_key": False}
                    ]
                },
                "Devices": {
                    "columns": [
                        {"name": "DeviceID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": True},
                        {"name": "DeviceName", "data_type": "varchar", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "DeviceType", "data_type": "varchar", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "DoorID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                        {"name": "IPAddress", "data_type": "varchar", "is_nullable": "YES", "default_value": None, "is_primary_key": False}
                    ]
                }
            }
            
            # Örnek ilişkiler
            relationships = [
                {"from_table": "Users", "from_column": "DepartmentID", "to_table": "Departments", "to_column": "DepartmentID"},
                {"from_table": "AccessLogs", "from_column": "UserID", "to_table": "Users", "to_column": "UserID"},
                {"from_table": "AccessLogs", "from_column": "DoorID", "to_table": "Doors", "to_column": "DoorID"},
                {"from_table": "AccessLogs", "from_column": "DeviceID", "to_table": "Devices", "to_column": "DeviceID"},
                {"from_table": "Permissions", "from_column": "UserID", "to_table": "Users", "to_column": "UserID"},
                {"from_table": "Permissions", "from_column": "DoorID", "to_table": "Doors", "to_column": "DoorID"},
                {"from_table": "Devices", "from_column": "DoorID", "to_table": "Doors", "to_column": "DoorID"}
            ]
        
        return {
            'tables': tables,
            'relationships': relationships
        }
    except Exception as e:
        print(f"Şema hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Eğer veritabanı bağlantısı yoksa örnek veriler dön
        tables = {
            "Users": {
                "columns": [
                    {"name": "UserID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": True},
                    {"name": "UserName", "data_type": "varchar", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                    {"name": "Email", "data_type": "varchar", "is_nullable": "YES", "default_value": None, "is_primary_key": False},
                    {"name": "DepartmentID", "data_type": "int", "is_nullable": "YES", "default_value": None, "is_primary_key": False}
                ]
            },
            "Departments": {
                "columns": [
                    {"name": "DepartmentID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": True},
                    {"name": "DepartmentName", "data_type": "varchar", "is_nullable": "NO", "default_value": None, "is_primary_key": False}
                ]
            },
            "AccessLogs": {
                "columns": [
                    {"name": "LogID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": True},
                    {"name": "UserID", "data_type": "int", "is_nullable": "NO", "default_value": None, "is_primary_key": False},
                    {"name": "AccessTime", "data_type": "datetime", "is_nullable": "NO", "default_value": None, "is_primary_key": False}
                ]
            }
        }
        
        relationships = [
            {"from_table": "Users", "from_column": "DepartmentID", "to_table": "Departments", "to_column": "DepartmentID"},
            {"from_table": "AccessLogs", "from_column": "UserID", "to_table": "Users", "to_column": "UserID"}
        ]
        
        return {'tables': tables, 'relationships': relationships}

def chat_with_database(user_message):
    """Kullanıcının veritabanı hakkındaki sorularını yanıtlar"""
    try:
        # Kullanıcı mesajında anahtar kelimeleri kontrol et
        message_lower = user_message.lower()
        
        # Kapılarla ilgili istatistikler
        if any(keyword in message_lower for keyword in ["kapı", "kapi", "gate"]):
            try:
                # Kapı istatistikleri sorgusu
                query = """
                SELECT 
                    g.GateName, 
                    COUNT(m.ID) as MovementCount
                FROM Gates g
                LEFT JOIN Movements m ON g.ID = m.GateID
                GROUP BY g.GateName, g.ID
                ORDER BY MovementCount DESC
                """
                
                results = execute_query(query)
                
                if results and len(results) > 0:
                    response = "Kapı İstatistikleri:\n\n"
                    for i, row in enumerate(results, 1):
                        gate_name = row[0]
                        movement_count = row[1]
                        response += f"{i}. {gate_name}: {movement_count} hareket\n"
                    
                    # Toplam kapı sayısı
                    response += f"\nToplam {len(results)} kapı bulunmaktadır."
                    
                    # En çok kullanılan kapılar
                    if len(results) > 0:
                        most_used = results[0]
                        response += f"\n\nEn çok kullanılan kapı: {most_used[0]} ({most_used[1]} hareket)"
                    
                    return response
                else:
                    return "Veritabanında kapı istatistikleri bulunamadı."
                    
            except Exception as e:
                print(f"Kapı sorgusu hatası: {str(e)}")
                
                # Alternatif sorgulama deneyin
                try:
                    # Sadece kapıları listele
                    query = "SELECT GateName, Description FROM Gates"
                    results = execute_query(query)
                    
                    if results and len(results) > 0:
                        response = "Sistemdeki Kapılar:\n\n"
                        for i, row in enumerate(results, 1):
                            gate_name = row[0]
                            description = row[1] if row[1] else "Açıklama yok"
                            response += f"{i}. {gate_name}: {description}\n"
                        
                        return response
                    else:
                        return "Veritabanında kapı bilgisi bulunamadı."
                except:
                    # Tüm tablolar arasında kapı kelimesi içeren tabloları bul
                    schema_data = get_database_schema()
                    gate_tables = [table for table in schema_data['tables'].keys() 
                                if "gate" in table.lower() or "kapi" in table.lower()]
                    
                    response = "Veritabanında kapılarla ilgili şu tablolar bulunmaktadır:\n\n"
                    for table in gate_tables:
                        response += f"- {table}\n"
                    
                    response += "\nDetaylı istatistikler için veritabanı bağlantınızı kontrol edin."
                    return response
        
        # Kullanıcı istatistikleri
        elif any(keyword in message_lower for keyword in ["kullanıcı", "kullanici", "user", "personel"]):
            try:
                # Kullanıcı istatistikleri sorgusu
                query = """
                SELECT TOP 10
                    u.UserName, 
                    COUNT(m.ID) as MovementCount
                FROM Users u
                LEFT JOIN Movements m ON u.ID = m.UserID
                GROUP BY u.UserName, u.ID
                ORDER BY MovementCount DESC
                """
                
                results = execute_query(query)
                
                if results and len(results) > 0:
                    response = "En Aktif 10 Kullanıcı:\n\n"
                    for i, row in enumerate(results, 1):
                        user_name = row[0]
                        movement_count = row[1]
                        response += f"{i}. {user_name}: {movement_count} hareket\n"
                    
                    return response
                else:
                    return "Veritabanında kullanıcı istatistikleri bulunamadı."
            except Exception as e:
                print(f"Kullanıcı sorgusu hatası: {str(e)}")
                return f"Kullanıcı istatistikleri alınırken bir hata oluştu: {str(e)}"
        
        # Genel veritabanı bilgisi
        else:
            # Veritabanı şemasını al
            schema_data = get_database_schema()
            table_count = len(schema_data['tables'])
            
            # İlk 5 tabloyu seç
            top_tables = list(schema_data['tables'].keys())[:5]
            
            # İlişki sayısını al
            relation_count = len(schema_data.get('relationships', []))
            
            response = f"Veritabanı Özeti:\n\n"
            response += f"- Toplam Tablo Sayısı: {table_count}\n"
            response += f"- İlişki Sayısı: {relation_count}\n\n"
            
            response += "Önemli Tablolar:\n"
            for table in top_tables:
                response += f"- {table}\n"
            
            response += "\nBelirli bir tablo hakkında detaylı bilgi için 'table_name hakkında bilgi ver' şeklinde sorun."
            return response
            
    except Exception as e:
        print(f"Chat sorgusu hatası: {str(e)}")
        return f"Üzgünüm, veritabanı sorgunuz işlenirken bir hata oluştu: {str(e)}"

def generate_sql_for_question(question):
    """Kullanıcının sorusuna göre SQL sorgusu önerir"""
    try:
        # Veritabanı şemasını al
        schema_data = get_database_schema()
        
        # Şema bilgilerini formatlı bir şekilde hazırla
        schema_info = "Veritabanı Tabloları ve Sütunları:\n\n"
        
        for table_name, table_data in schema_data['tables'].items():
            schema_info += f"Tablo: {table_name}\n"
            schema_info += "Sütunlar:\n"
            
            for column in table_data.get('columns', []):
                pk_mark = "🔑 " if column.get('is_primary_key') else ""
                col_name = column.get('name', '')
                data_type = column.get('data_type', '')
                
                schema_info += f"  - {pk_mark}{col_name} ({data_type})\n"
            
            schema_info += "\n"
        
        # İlişkileri ekle
        schema_info += "Tablo İlişkileri:\n\n"
        for rel in schema_data.get('relationships', []):
            schema_info += f"{rel.get('from_table')}.{rel.get('from_column')} -> {rel.get('to_table')}.{rel.get('to_column')}\n"
        
        # Gemini'ye sorguyu ve veritabanı bilgilerini gönder
        prompt = f"""
        Sen bir SQL uzmanısın. Aşağıdaki veritabanı şeması bilgilerini kullanarak, kullanıcının sorusuna uygun bir SQL sorgusu oluştur:
        
        {schema_info}
        
        Kullanıcı sorusu: {question}
        
        Sadece SQL sorgusunu oluştur, başka açıklama yapma. Gerekirse JOIN işlemleri ekle.
        """
        
        # Gemini'den yanıt al
        sql_query = analyze_with_gemini(prompt)
        
        # SQL sorgusunu döndür
        if isinstance(sql_query, dict) and "error" in sql_query:
            return None
        
        # SQL etiketlerini temizle
        if sql_query:
            sql_query = sql_query.strip()
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        return sql_query
    except Exception as e:
        print(f"SQL oluşturma hatası: {str(e)}")
        return None

def execute_generated_sql(question):
    """Kullanıcının sorusuna göre SQL oluşturur ve çalıştırır"""
    try:
        # Basit SQL sorgularını algıla
        query = None
        
        # Basit anahtar kelime analizi yap
        question_lower = question.lower()
        
        if "kullanıcı" in question_lower or "user" in question_lower:
            if "tüm" in question_lower or "hepsi" in question_lower or "listele" in question_lower:
                query = "SELECT * FROM Users"
        
        elif "kapı" in question_lower or "door" in question_lower:
            if "tüm" in question_lower or "hepsi" in question_lower or "listele" in question_lower:
                query = "SELECT * FROM Doors"
        
        elif "log" in question_lower or "erişim" in question_lower or "access" in question_lower:
            if "son" in question_lower or "recent" in question_lower:
                query = "SELECT TOP 20 * FROM AccessLogs ORDER BY AccessTime DESC"
            else:
                query = "SELECT * FROM AccessLogs"
        
        # Sorgu oluşturulamadıysa hata döndür
        if not query:
            return {"error": "Sorunuz için uygun bir SQL sorgusu oluşturulamadı. Lütfen daha açık bir soru sorun."}
        
        # SQL sorgusunu çalıştır
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(query)
        
        # Sonuçları al
        results = cursor.fetchall()
        
        # Sütun isimlerini al
        columns = [column[0] for column in cursor.description]
        
        # Sonuçları formatla
        formatted_results = []
        for row in results:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            formatted_results.append(row_dict)
        
        cursor.close()
        conn.close()
        
        return {
            "query": query,
            "analysis": f"Bu sorgu '{question}' için oluşturulmuştur.",
            "columns": columns,
            "results": formatted_results,
            "count": len(formatted_results)
        }
    except Exception as e:
        print(f"SQL çalıştırma hatası: {str(e)}")
        return {
            "error": f"SQL sorgusu çalıştırılırken bir hata oluştu: {str(e)}",
            "query": query if locals().get('query') else None
        } 