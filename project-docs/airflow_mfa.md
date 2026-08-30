# Airflow → Snowflake MFA / Key-Pair Authentication Setup

This guide configures Airflow to connect to Snowflake using a dedicated RSA key pair, while keeping the existing Snowflake connection and public key untouched.

## Final Architecture

```text
                 SNOWFLAKE USER
                  VISHNU1702
                       │
             ┌─────────┴─────────┐
             │                   │
    RSA_PUBLIC_KEY       RSA_PUBLIC_KEY_2
             │                   │
             ▼                   ▼
    Existing connection      Airflow
                                  │
                           snowflake_airflow
                                  │
                           private_key_file
                                  │
                                  ▼
                  /opt/airflow/keys/
                  airflow_snowflake_key.p8
```

## 1. Keep the Existing Key

Do **not** modify:

```text
RSA_PUBLIC_KEY
```

Your existing application/connection should continue using the existing key.

Airflow will use:

```text
RSA_PUBLIC_KEY_2
```

This avoids breaking the existing connection.

---

## 2. Create a New Key Pair for Airflow

From the Airflow project directory:

```bash
mkdir -p airflow/keys

openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out airflow/keys/airflow_snowflake_key.p8 -nocrypt

openssl rsa -in airflow/keys/airflow_snowflake_key.p8 -pubout -out airflow/keys/airflow_snowflake_key.pub
```

Files:

```text
airflow/keys/
├── airflow_snowflake_key.p8      # PRIVATE KEY
└── airflow_snowflake_key.pub     # PUBLIC KEY
```

The private key should look like:

```text
-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----
```

The public key should look like:

```text
-----BEGIN PUBLIC KEY-----
...
-----END PUBLIC KEY-----
```

Never share or commit the private `.p8` file.

Protect it:

```bash
chmod 600 airflow/keys/airflow_snowflake_key.p8
```

Add the private key to `.gitignore`:

```gitignore
airflow/keys/*.p8
```

---

## 3. Mount the Key into Docker Airflow

In `docker-compose.yml`, make the local `keys` directory available inside Airflow:

```yaml
volumes:
  - ./dags:/opt/airflow/dags
  - ./keys:/opt/airflow/keys:ro
```

The important mapping is:

```text
Local:
./keys/airflow_snowflake_key.p8

Docker:
 /opt/airflow/keys/airflow_snowflake_key.p8
```

Verify from the scheduler container:

```bash
docker compose exec scheduler ls -l /opt/airflow/keys/airflow_snowflake_key.p8
```

Expected:

```text
-rw------- ... /opt/airflow/keys/airflow_snowflake_key.p8
```

---

## 4. Register the New Public Key in Snowflake

Extract the public key from the private key:

```bash
openssl rsa -in airflow/keys/airflow_snowflake_key.p8 -pubout
```

Copy the Base64 contents between:

```text
-----BEGIN PUBLIC KEY-----
...
-----END PUBLIC KEY-----
```

Then in Snowflake:

```sql
ALTER USER VISHNU1702
SET RSA_PUBLIC_KEY_2='YOUR_NEW_PUBLIC_KEY';
```

Do **not** change:

```text
RSA_PUBLIC_KEY
```

The existing key remains available for the existing connection.

---

## 5. Verify Both Snowflake Keys

Run:

```sql
DESC USER VISHNU1702;
```

Verify that the user has:

```text
RSA_PUBLIC_KEY
RSA_PUBLIC_KEY_2
```

The first is the existing key.

The second is the new Airflow key.

---

## 6. Create a Separate Airflow Connection

Create a new connection rather than modifying `snowflake_default`.

Connection ID:

```text
snowflake_airflow
```

Connection type:

```text
Snowflake
```

Login:

```text
VISHNU1702
```

Password:

```text
Leave empty
```

Extra:

```json
{
  "account": "GOOQRSO-QS17645",
  "warehouse": "ZOMATO_WH",
  "database": "ZOMATO",
  "schema": "RAW",
  "role": "DBT_ROLE",
  "private_key_file": "/opt/airflow/keys/airflow_snowflake_key.p8"
}
```

Verify from the scheduler:

```bash
docker compose exec scheduler airflow connections get snowflake_airflow
```

The output should contain:

```text
private_key_file
```

with:

```text
/opt/airflow/keys/airflow_snowflake_key.p8
```

The connection should have no password.

---

## 7. Change the DAG Connection

Change the Snowflake connection in the DAG from:

```python
conn_id="snowflake_default"
```

to:

```python
conn_id="snowflake_airflow"
```

Example:

```python
reload_raw = SQLExecuteQueryOperator(
    task_id="reload_raw",
    conn_id="snowflake_airflow",
    sql=COPY_RAW,
    split_statements=True,
    autocommit=True
)
```

The DAG does not need to contain the private key.

---

## 8. Fix the COPY Statement Typo

Make sure the reviews statement has a space after `INTO`.

Incorrect:

```python
"COPY INTOZOMATO.RAW.reviews FROM @ZOMATO.RAW.ZOMATO_RAW_STAGE/reviews/"
```

Correct:

```python
"COPY INTO ZOMATO.RAW.reviews FROM @ZOMATO.RAW.ZOMATO_RAW_STAGE/reviews/"
```

---

## 9. Restart Airflow

After Docker Compose changes:

```bash
docker compose down
docker compose up -d
```

Check:

```bash
docker compose ps
```

The scheduler should show:

```text
Up
```

---

## 10. Test the DAG

Trigger `zomato_batch` from the Airflow UI.

The authentication flow should now be:

```text
Airflow
   │
   │ airflow_snowflake_key.p8
   ▼
Snowflake
   │
   │ matches
   ▼
RSA_PUBLIC_KEY_2
```

The automated connection should use key-pair authentication instead of password + TOTP.

---

## Troubleshooting

### Error: `MFA with TOTP is required`

This usually means the connection is still attempting password authentication.

Check:

```bash
docker compose exec scheduler airflow connections get snowflake_airflow
```

Confirm:

```text
password = None
```

and:

```text
private_key_file = /opt/airflow/keys/airflow_snowflake_key.p8
```

### Error: `No such file or directory`

Check:

```bash
docker compose exec scheduler ls -l /opt/airflow/keys/airflow_snowflake_key.p8
```

If missing, check the Docker Compose volume:

```yaml
- ./keys:/opt/airflow/keys:ro
```

### Key authentication/JWT error

If the private key is found but authentication fails, verify that the corresponding public key was registered as:

```sql
RSA_PUBLIC_KEY_2
```

for the same Snowflake user.

### Existing Snowflake connection

Do not replace:

```text
RSA_PUBLIC_KEY
```

The purpose of `RSA_PUBLIC_KEY_2` is to allow the new Airflow key to coexist with the existing key.

---

## Important Security Notes

- Never paste the private `.p8` key into chat.
- Never commit the `.p8` key to Git.
- Keep the private key readable only by the required Airflow process.
- Do not put the private key directly into the DAG.
- Do not delete or replace the existing `RSA_PUBLIC_KEY` while the old connection is still needed.
