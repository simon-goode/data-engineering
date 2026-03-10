import json
import os
from datetime import datetime, timedelta, timezone

import psycopg2
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

API_URL = os.getenv("MBTA_API_URL", "https://api-v3.mbta.com/vehicles")
MAX_SNAPSHOTS = int(os.getenv("MBTA_MAX_SNAPSHOTS", "300"))  # 5 minutes at 1s intervals

TARGET_DB = {
    "host": os.getenv("MBTA_TARGET_DB_HOST", "postgres-1"),
    "port": int(os.getenv("MBTA_TARGET_DB_PORT", "5432")),
    "dbname": os.getenv("MBTA_TARGET_DB_NAME", "postgres"),
    "user": os.getenv("MBTA_TARGET_DB_USER", "postgres"),
    "password": os.getenv("MBTA_TARGET_DB_PASSWORD", "postgres"),
}


def _normalize_vehicle(vehicle: dict, ingested_at: datetime) -> tuple:
    attributes = vehicle.get("attributes", {})
    relationships = vehicle.get("relationships", {})

    # Safely extract relationship IDs, handling None values
    route_data = relationships.get("route", {}).get("data")
    route_id = route_data.get("id") if route_data else None
    
    stop_data = relationships.get("stop", {}).get("data")
    stop_id = stop_data.get("id") if stop_data else None
    
    trip_data = relationships.get("trip", {}).get("data")
    trip_id = trip_data.get("id") if trip_data else None

    return (
        ingested_at,
        vehicle.get("id"),
        attributes.get("label"),
        attributes.get("current_status"),
        attributes.get("current_stop_sequence"),
        attributes.get("direction_id"),
        attributes.get("latitude"),
        attributes.get("longitude"),
        attributes.get("bearing"),
        attributes.get("speed"),
        attributes.get("updated_at"),
        route_id,
        stop_id,
        trip_id,
        json.dumps(vehicle),
    )


def fetch_transform_load() -> None:
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    payload = response.json()

    vehicles = payload.get("data", [])
    ingested_at = datetime.now(timezone.utc)

    if not vehicles:
        return

    records = [_normalize_vehicle(vehicle, ingested_at) for vehicle in vehicles]

    ddl = """
    CREATE TABLE IF NOT EXISTS mbta.dim_vehicle_snapshots (
      ingested_at TIMESTAMPTZ NOT NULL,
      vehicle_id TEXT NOT NULL,
      label TEXT,
      current_status TEXT,
      current_stop_sequence INTEGER,
      direction_id INTEGER,
      latitude DOUBLE PRECISION,
      longitude DOUBLE PRECISION,
      bearing DOUBLE PRECISION,
      speed DOUBLE PRECISION,
      vehicle_updated_at TIMESTAMPTZ,
      route_id TEXT,
      stop_id TEXT,
      trip_id TEXT,
      raw_payload JSONB NOT NULL,
      PRIMARY KEY (ingested_at, vehicle_id)
    );
    """

    insert_sql = """
    INSERT INTO mbta.dim_vehicle_snapshots (
      ingested_at,
      vehicle_id,
      label,
      current_status,
      current_stop_sequence,
      direction_id,
      latitude,
      longitude,
      bearing,
      speed,
      vehicle_updated_at,
      route_id,
      stop_id,
      trip_id,
      raw_payload
    ) VALUES (
      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    ) ON CONFLICT (ingested_at, vehicle_id) DO NOTHING;
    """

    purge_sql = """
    DELETE FROM mbta.dim_vehicle_snapshots
    WHERE ingested_at < (
      SELECT ingested_at FROM (
        SELECT DISTINCT ingested_at
        FROM mbta.dim_vehicle_snapshots
        ORDER BY ingested_at DESC
        LIMIT %s
      ) AS recent
      ORDER BY ingested_at ASC
      LIMIT 1
    );
    """

    with psycopg2.connect(**TARGET_DB) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            cur.executemany(insert_sql, records)
            cur.execute(purge_sql, (MAX_SNAPSHOTS,))


default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(seconds=15),
}

with DAG(
    dag_id="mbta_vehicles_ingestion",
    description="Poll MBTA /vehicles every 1 second and load snapshots into Postgres",
    default_args=default_args,
    start_date=datetime(2026, 3, 1),
    schedule=timedelta(seconds=1),
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=True,
    tags=["mbta", "ingestion", "postgres"],
) as dag:
    ingest_task = PythonOperator(
        task_id="fetch_transform_load_mbta_vehicles",
        python_callable=fetch_transform_load,
    )

    ingest_task
