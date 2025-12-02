# 📊 Guía de Configuración de Base de Datos - EasyGrow Consumer

## Requisitos Previos
- PostgreSQL instalado en tu sistema
- Acceso a la terminal/cmd
- Usuario root o permisos de superusuario en PostgreSQL

---

## ⚙️ Pasos para Configurar la Base de Datos

### **Paso 1: Instalar PostgreSQL (si no está instalado)**

#### En Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

#### En macOS (con Homebrew):
```bash
brew install postgresql
```

#### En Windows:
Descargar e instalar desde: https://www.postgresql.org/download/windows/

---

### **Paso 2: Iniciar el servicio PostgreSQL**

#### En Linux:
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Para que inicie automáticamente
```

#### En macOS:
```bash
brew services start postgresql
```

#### En Windows:
El servicio debería iniciarse automáticamente después de la instalación.

---

### **Paso 3: Acceder a PostgreSQL**

Abre una terminal y accede a PostgreSQL como usuario `postgres`:

```bash
sudo -u postgres psql
```

En Windows (en Command Prompt):
```cmd
psql -U postgres
```

Verás el prompt de PostgreSQL:
```
postgres=#
```

---

### **Paso 4: Crear el usuario de la base de datos**

```sql
CREATE USER easygrow WITH PASSWORD 'tu_contraseña_segura';
ALTER ROLE easygrow CREATEDB;
```

**Reemplaza `tu_contraseña_segura` con una contraseña real** ⚠️

---

### **Paso 5: Crear la base de datos**

```sql
CREATE DATABASE easygrow_db OWNER easygrow;
```

---

### **Paso 6: Salir de PostgreSQL**

```sql
\q
```

---

### **Paso 7: Ejecutar el script SQL**

Ahora ejecuta el script desde tu terminal (fuera de PostgreSQL):

#### Opción A: Usando psql directamente
```bash
psql -U easygrow -d easygrow_db -f database_setup.sql
```

Ingresa tu contraseña cuando se solicite.

#### Opción B: Desde el directorio del proyecto
```bash
cd /home/hector/Escritorio/integrador-6C
psql -U easygrow -d easygrow_db -f database_setup.sql
```

**Deberías ver mensajes como:**
```
CREATE TABLE
CREATE INDEX
CREATE VIEW
```

---

## 🔧 Configurar variables de entorno

Actualiza tu archivo `.env` con los valores de conexión:

```env
DB_HOST=localhost
DB_USER=easygrow
DB_PASS=tu_contraseña_segura
DB_SCHEMA=easygrow_db
BD_PORT=5432
```

**Asegúrate de que coincidan con los valores que creaste en los pasos anteriores.**

---

## ✅ Verificar que todo está funcionando

### Desde PostgreSQL:
```bash
psql -U easygrow -d easygrow_db
```

Dentro de PostgreSQL:
```sql
\dt  -- Lista todas las tablas
\di  -- Lista todos los índices
\dv  -- Lista todas las vistas
```

Deberías ver:
- **Tablas**: dispositivos, sensores, datos_sensores, eventos_bomba
- **Índices**: varios índices para optimización
- **Vistas**: v_ultimos_datos_sensores, v_ultimos_eventos_bomba

---

## 🧪 Prueba tu aplicación

Una vez completados todos los pasos:

```bash
cd /home/hector/Escritorio/integrador-6C
python main.py
```

Si la conexión es exitosa, deberías ver:
```
✅ Conexión exitosa a PostgreSQL
🚀 Iniciando EasyGrow Consumer...
```

---

## 🆘 Solución de Problemas

### Error: "could not connect to server"
- Verifica que PostgreSQL está corriendo: `sudo systemctl status postgresql`
- Comprueba que DB_HOST es `localhost` o `127.0.0.1`

### Error: "FATAL: Ident authentication failed"
- Verifica que usas el usuario correcto (`easygrow`)
- Comprueba la contraseña en `.env`

### Error: "database does not exist"
- Verifica que creaste la base de datos: `psql -U easygrow -d easygrow_db -c "\l"`

### Error: "permission denied"
- En Linux, usa: `sudo -u postgres psql` para acceder como administrador

---

### Error: "la autentificación password falló" / problemas con `pg_hba.conf`

Si al ejecutar `python main.py` ves un error tipo:

```
psycopg2.OperationalError: connection to server at "<HOST>", port 5432 failed: FATAL:  la autentificación password falló para el usuario "<usuario>"
```

Pasos recomendados:

1. Verifica tu archivo `.env` en el proyecto y asegúrate de que `DB_USER`, `DB_PASS` y `DB_SCHEMA` correspondan al usuario y base de datos que existen en el servidor PostgreSQL. No uses `postgres` en producción; crea un usuario dedicado como `easygrow`.

2. Desde tu equipo cliente prueba la conexión manualmente con `psql` (sustituye host, usuario, base y contraseña):

```bash
# Opción interactiva (te pedirá contraseña)
psql -h 10.198.99.27 -U easygrow -d easygrow -W

# Opción no interactiva usando variable de entorno (temporal)
export PGPASSWORD='tu_contraseña_segura'
psql -h 10.198.99.27 -U easygrow -d easygrow -c "SELECT current_user, current_database();"
unset PGPASSWORD
```

3. Si la autenticación falla, ajusta/crea la entrada en el `pg_hba.conf` del servidor PostgreSQL (ejecutar en el servidor):

```bash
sudo -u postgres psql -c "SHOW hba_file;"
# Edita el archivo mostrado y añade por ejemplo:
# host    easygrow    easygrow    10.198.99.218/32    scram-sha-256
# o (más general, menos recomendable):
# host    all         all         10.198.99.218/32    md5

# Después recarga la configuración:
sudo -u postgres psql -c "SELECT pg_reload_conf();"
```

4. Si deseas cambiar la contraseña de un usuario (servidor):

```bash
# En el servidor PostgreSQL
sudo -u postgres psql -c "ALTER USER easygrow WITH PASSWORD 'nueva_contraseña_segura';"
```

5. Asegúrate que `pg_hba.conf` tenga la entrada adecuada **antes** de la regla más general (`host all all 0.0.0.0/0 ...`), ya que PostgreSQL aplica la primera línea que coincide.

6. Si tu `pg_hba.conf` usa `scram-sha-256`, confirma que la versión del cliente/psycopg2 soporta SCRAM (psycopg2 moderno sí lo soporta). Si no, usa `md5` o actualiza los drivers.

7. Finalmente, actualiza tu `.env` con las credenciales correctas y reinicia la aplicación:

```bash
source integrador/bin/activate
python main.py
```

Si quieres, pega aquí la salida del comando `psql -h 10.198.99.27 -U easygrow -d easygrow -W` (o el error) y te guío en el siguiente paso.

## 📋 Resumen rápido (después de la primera vez)

Para iniciar tu aplicación en futuras ocasiones:

```bash
# 1. Asegúrate de que PostgreSQL está corriendo
sudo systemctl start postgresql

# 2. Ejecuta tu aplicación
cd /home/hector/Escritorio/integrador-6C
python main.py
```

---

**¡Listo! Tu base de datos está configurada y lista para usar.** 🎉
