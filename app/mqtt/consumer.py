import json
import logging

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.workflow import run_alarm_workflow

logger = logging.getLogger(__name__)


class AlarmConsumer:
    def __init__(self) -> None:
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if settings.MQTT_USERNAME:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code == 0:
            client.subscribe(settings.MQTT_TOPIC, qos=1)
            logger.info("MQTT subscribed to %s", settings.MQTT_TOPIC)
        else:
            logger.error("MQTT connection failed: %s", reason_code)

    def _on_message(self, client, userdata, message) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            with SessionLocal() as db:
                execution = run_alarm_workflow(db, payload, trigger_type="mqtt")
                logger.info("MQTT workflow %s: %s", execution.execution_id, execution.status)
        except Exception:
            logger.exception("Failed to process MQTT alarm")

    def start(self) -> None:
        self.client.connect_async(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
        self.client.loop_start()

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
