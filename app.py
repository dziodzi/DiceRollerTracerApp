from flask import Flask, jsonify
from random import randint, choice
from time import sleep
import json
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import ReadableSpan

provider = TracerProvider(
    resource=Resource.create({SERVICE_NAME: "dice-roller-app"})
)
trace.set_tracer_provider(provider)

console_processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(console_processor)

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

jaeger_processor = BatchSpanProcessor(jaeger_exporter)
provider.add_span_processor(jaeger_processor)

tracer = trace.get_tracer(__name__)
app = Flask(__name__)

class CustomSpanProcessor(BatchSpanProcessor):
    def on_end(self, span: ReadableSpan):
        trace_data = {
            "name": span.name,
            "start_time": span.start_time,
            "end_time": span.end_time,
            "attributes": dict(span.attributes),
            "status": span.status.status_code.name,
            "events": [
                {
                    "name": event.name,
                    "attributes": dict(event.attributes),
                    "timestamp": event.timestamp,
                } for event in span.events
            ],
        }
        try:
            with open("traces.json", "a") as trace_file:
                trace_file.write(json.dumps(trace_data) + "\n")
        except Exception as e:
            print(f"Failed to write trace to file: {e}")
        super().on_end(span)


provider.add_span_processor(CustomSpanProcessor(ConsoleSpanExporter()))


def roll():
    return randint(1, 6)


def simulate_random_behavior():
    action = choice(["delay", "success", "success", "success", "error"])
    if action == "delay":
        sleep_time = randint(1, 3)
        sleep(sleep_time)
    elif action == "error":
        raise ValueError("Simulated random error")


@app.route("/rolldice")
def roll_dice():
    try:
        with tracer.start_as_current_span("server_request") as span:
            for i in range(3):
                with tracer.start_as_current_span(f"processing_span_{i}") as child_span:
                    try:
                        simulate_random_behavior()
                        result = roll()
                        child_span.set_attribute("result", result)
                        child_span.set_attribute("iteration", i)
                    except Exception as e:
                        child_span.record_exception(e)
                        child_span.set_status(trace.status.Status(trace.status.StatusCode.ERROR))
                        return jsonify({"error": str(e)}), 500

            span.set_attribute("endpoint", "/rolldice")
            span.set_attribute("method", "GET")
            return jsonify({"result": roll()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
