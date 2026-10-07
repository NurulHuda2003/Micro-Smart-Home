import json
import logging

from datetime import datetime

from flask import (
    Flask,
    jsonify,
    request
)

from config import (
    WEB_HOST,
    WEB_PORT,
    PIR2_SCHEDULE_FILE,
    PIR2_DEFAULT_ENABLED,
    PIR2_DEFAULT_START,
    PIR2_DEFAULT_END
)

from system_state import (
    get_state,
    update_state
)


app = Flask(__name__)


logging.getLogger(
    "werkzeug"
).setLevel(
    logging.ERROR
)


# =========================================================
# PIR-2 SCHEDULE
# =========================================================

def valid_time(value):

    try:

        datetime.strptime(
            value,
            "%H:%M"
        )

        return True

    except Exception:

        return False


def load_pir2_schedule():

    enabled = PIR2_DEFAULT_ENABLED
    start = PIR2_DEFAULT_START
    end = PIR2_DEFAULT_END


    try:

        with open(
            PIR2_SCHEDULE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )


        enabled = bool(
            data.get(
                "enabled",
                enabled
            )
        )


        if valid_time(
            str(
                data.get(
                    "start_time",
                    start
                )
            )
        ):

            start = str(
                data.get(
                    "start_time"
                )
            )


        if valid_time(
            str(
                data.get(
                    "end_time",
                    end
                )
            )
        ):

            end = str(
                data.get(
                    "end_time"
                )
            )


    except Exception:

        pass


    update_state(
        pir2_enabled=enabled,
        pir2_start_time=start,
        pir2_end_time=end
    )


load_pir2_schedule()


# =========================================================
# DASHBOARD
# =========================================================

HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>Smart Home Dashboard</title>


<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f1f5f9;
    color: #0f172a;
}

header {
    background: #111827;
    color: white;
    padding: 25px;
    text-align: center;
}

header h1 {
    margin: 0 0 8px 0;
}

.container {
    width: 94%;
    max-width: 1250px;
    margin: 25px auto;
}

.section {
    background: white;
    padding: 22px;
    margin-bottom: 22px;
    border-radius: 14px;
    box-shadow: 0 3px 12px rgba(0,0,0,.08);
}

.title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
}

.title-row h2 {
    margin: 0;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(170px, 1fr)
        );
    gap: 14px;
}

.card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 17px;
    border-radius: 11px;
}

.label {
    color: #64748b;
    font-size: 13px;
    font-weight: bold;
}

.value {
    font-size: 22px;
    font-weight: bold;
    margin-top: 8px;
}

.badge {
    font-size: 12px;
    font-weight: bold;
    border-radius: 20px;
    padding: 7px 12px;
}

.green {
    background: #dcfce7;
    color: #166534;
}

.red {
    background: #fee2e2;
    color: #991b1b;
}

.controls {
    margin-top: 18px;
    display: grid;
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(180px, 1fr)
        );
    gap: 12px;
}

.control {
    display: flex;
    flex-direction: column;
    gap: 7px;
}

input[type="time"] {
    padding: 10px;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
}

button {
    border: 0;
    border-radius: 7px;
    padding: 11px;
    background: #2563eb;
    color: white;
    cursor: pointer;
    font-weight: bold;
}

footer {
    text-align: center;
    padding: 20px;
    color: #64748b;
}

</style>

</head>


<body>

<header>

<h1>
Smart Home Surveillance System
</h1>

<div>
Raspberry Pi + ESP32
</div>

</header>


<div class="container">


<!-- =================================================== -->
<!-- KITCHEN -->
<!-- =================================================== -->

<div class="section">

<div class="title-row">

<h2>
Kitchen Safety
</h2>

<span
    id="espBadge"
    class="badge red"
>
ESP32 OFFLINE
</span>

</div>


<div class="grid">

<div class="card">
<div class="label">Gas ADC</div>
<div class="value" id="gasADC">0</div>
</div>

<div class="card">
<div class="label">Approx Gas PPM</div>
<div class="value" id="gasPPM">0</div>
</div>

<div class="card">
<div class="label">Gas</div>
<div class="value" id="gas">SAFE</div>
</div>

<div class="card">
<div class="label">Flame</div>
<div class="value" id="flame">NO</div>
</div>

<div class="card">
<div class="label">Kitchen State</div>
<div class="value" id="kitchenState">WAITING</div>
</div>

<div class="card">
<div class="label">ESP32 Buzzer</div>
<div class="value" id="espBuzzer">OFF</div>
</div>

<div class="card">
<div class="label">Window</div>
<div class="value" id="window">CLOSED</div>
</div>

<div class="card">
<div class="label">ESP32 Data Age</div>
<div class="value" id="espAge">-</div>
</div>

</div>

</div>


<!-- =================================================== -->
<!-- SOLAR -->
<!-- =================================================== -->

<div class="section">

<div class="title-row">

<h2>
Solar Tracking & Energy
</h2>

<span
    id="solarBadge"
    class="badge red"
>
NO DATA
</span>

</div>


<div class="grid">

<div class="card">
<div class="label">Light</div>
<div class="value" id="light">UNKNOWN</div>
</div>

<div class="card">
<div class="label">Servo Angle</div>
<div class="value" id="solarAngle">90°</div>
</div>

<div class="card">
<div class="label">Direction</div>
<div class="value" id="direction">CENTER</div>
</div>

<div class="card">
<div class="label">Tracking</div>
<div class="value" id="tracking">STARTING</div>
</div>

<div class="card">
<div class="label">Voltage</div>
<div class="value" id="voltage">0.00 V</div>
</div>

<div class="card">
<div class="label">Current</div>
<div class="value" id="current">0.00 mA</div>
</div>

<div class="card">
<div class="label">Power</div>
<div class="value" id="power">0.000 W</div>
</div>

</div>

</div>


<!-- =================================================== -->
<!-- FACE SECURITY -->
<!-- =================================================== -->

<div class="section">

<div class="title-row">

<h2>
Main Gate Security - PIR 1
</h2>

<span class="badge green">
RASPBERRY PI
</span>

</div>


<div class="grid">

<div class="card">
<div class="label">Motion</div>
<div class="value" id="motion">NONE</div>
</div>

<div class="card">
<div class="label">Camera</div>
<div class="value" id="camera">OFF</div>
</div>

<div class="card">
<div class="label">Face Status</div>
<div class="value" id="face">WAITING</div>
</div>

<div class="card">
<div class="label">Person</div>
<div class="value" id="person">-</div>
</div>

<div class="card">
<div class="label">Score</div>
<div class="value" id="score">0.000</div>
</div>

<div class="card">
<div class="label">Gate</div>
<div class="value" id="gate">LOCKED</div>
</div>

<div class="card">
<div class="label">Security Buzzer</div>
<div class="value" id="piBuzzer">OFF</div>
</div>

</div>

</div>


<!-- =================================================== -->
<!-- PIR-2 -->
<!-- =================================================== -->

<div class="section">

<div class="title-row">

<h2>
Scheduled Security - PIR 2
</h2>

<span
    id="pir2Badge"
    class="badge red"
>
DISABLED
</span>

</div>


<div class="grid">

<div class="card">
<div class="label">Schedule Status</div>
<div class="value" id="pir2Status">DISABLED</div>
</div>

<div class="card">
<div class="label">Motion</div>
<div class="value" id="pir2Motion">NONE</div>
</div>

<div class="card">
<div class="label">Schedule</div>
<div class="value" id="pir2Schedule">22:00 - 06:00</div>
</div>

</div>


<div class="controls">

<div class="control">

<label>
<input
    type="checkbox"
    id="pir2Enabled"
>
Enable PIR-2
</label>

</div>


<div class="control">

<label>
Start Time
</label>

<input
    type="time"
    id="pir2Start"
>

</div>


<div class="control">

<label>
End Time
</label>

<input
    type="time"
    id="pir2End"
>

</div>


<div class="control">

<label>Save</label>

<button onclick="saveSchedule()">
Save Schedule
</button>

</div>

</div>


<p id="saveMessage"></p>

</div>


</div>


<footer>
Dashboard updates every 500 ms
</footer>


<script>

let formLoaded = false;


function setText(id, value)
{
    const e =
        document.getElementById(id);

    if (e)
    {
        e.textContent = value;
    }
}


function updateESPBadge(connected)
{
    const badge =
        document.getElementById(
            "espBadge"
        );


    if (connected)
    {
        badge.textContent =
            "ESP32 CONNECTED";

        badge.className =
            "badge green";
    }

    else
    {
        badge.textContent =
            "ESP32 OFFLINE";

        badge.className =
            "badge red";
    }
}


function updateSolarBadge(
    connected,
    tracking
)
{
    const badge =
        document.getElementById(
            "solarBadge"
        );


    if (!connected)
    {
        badge.textContent =
            "NO DATA";

        badge.className =
            "badge red";

        return;
    }


    badge.textContent =
        tracking || "CONNECTED";

    badge.className =
        "badge green";
}


function updatePir2Badge(
    enabled,
    active
)
{
    const badge =
        document.getElementById(
            "pir2Badge"
        );


    if (!enabled)
    {
        badge.textContent =
            "DISABLED";

        badge.className =
            "badge red";
    }

    else if (active)
    {
        badge.textContent =
            "ACTIVE";

        badge.className =
            "badge green";
    }

    else
    {
        badge.textContent =
            "SCHEDULE OFF";

        badge.className =
            "badge red";
    }
}


async function refresh()
{
    try
    {
        const response =
            await fetch(
                "/api/status?t="
                +
                Date.now()
            );


        const d =
            await response.json();


        // ESP32

        updateESPBadge(
            d.esp32_connected
        );


        setText(
            "gasADC",
            d.gas_adc
        );


        setText(
            "gasPPM",
            d.gas_ppm
        );


        setText(
            "gas",
            d.gas_detected
            ?
            "DETECTED"
            :
            "SAFE"
        );


        setText(
            "flame",
            d.flame_detected
            ?
            "FIRE"
            :
            "NO"
        );


        setText(
            "kitchenState",
            d.esp32_state
        );


        setText(
            "espBuzzer",
            d.esp32_buzzer
        );


        setText(
            "window",
            d.window
        );


        setText(
            "espAge",
            d.esp32_age === null
            ?
            "-"
            :
            d.esp32_age + " sec"
        );


        // Solar

        setText(
            "light",
            d.light_status
        );


        setText(
            "solarAngle",
            Number(
                d.solar_servo_angle || 0
            )
            +
            "°"
        );


        setText(
            "direction",
            d.solar_direction
        );


        setText(
            "tracking",
            d.solar_tracking
        );


        setText(
            "voltage",
            Number(
                d.solar_voltage || 0
            ).toFixed(2)
            +
            " V"
        );


        setText(
            "current",
            Number(
                d.solar_current || 0
            ).toFixed(2)
            +
            " mA"
        );


        setText(
            "power",
            Number(
                d.solar_power || 0
            ).toFixed(3)
            +
            " W"
        );


        updateSolarBadge(
            d.esp32_connected,
            d.solar_tracking
        );


        // PIR-1

        setText(
            "motion",
            d.motion
            ?
            "DETECTED"
            :
            "NONE"
        );


        setText(
            "camera",
            d.camera
        );


        setText(
            "face",
            d.face_status
        );


        setText(
            "person",
            d.person
        );


        setText(
            "score",
            Number(
                d.face_score || 0
            ).toFixed(3)
        );


        setText(
            "gate",
            d.gate
        );


        setText(
            "piBuzzer",
            d.pi_buzzer
        );


        // PIR-2

        updatePir2Badge(
            d.pir2_enabled,
            d.pir2_active
        );


        setText(
            "pir2Status",
            !d.pir2_enabled
            ?
            "DISABLED"
            :
            (
                d.pir2_active
                ?
                "ACTIVE"
                :
                "SCHEDULE OFF"
            )
        );


        setText(
            "pir2Motion",
            d.pir2_motion
            ?
            "DETECTED"
            :
            "NONE"
        );


        setText(
            "pir2Schedule",
            d.pir2_start_time
            +
            " - "
            +
            d.pir2_end_time
        );


        if (!formLoaded)
        {
            document.getElementById(
                "pir2Enabled"
            ).checked =
                d.pir2_enabled;


            document.getElementById(
                "pir2Start"
            ).value =
                d.pir2_start_time;


            document.getElementById(
                "pir2End"
            ).value =
                d.pir2_end_time;


            formLoaded = true;
        }
    }

    catch(error)
    {
        updateESPBadge(false);

        updateSolarBadge(
            false,
            ""
        );
    }
}


async function saveSchedule()
{
    const enabled =
        document.getElementById(
            "pir2Enabled"
        ).checked;


    const start =
        document.getElementById(
            "pir2Start"
        ).value;


    const end =
        document.getElementById(
            "pir2End"
        ).value;


    const message =
        document.getElementById(
            "saveMessage"
        );


    try
    {
        const response =
            await fetch(
                "/api/pir2/schedule",
                {
                    method: "POST",

                    headers:
                    {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            {
                                enabled:
                                    enabled,

                                start_time:
                                    start,

                                end_time:
                                    end
                            }
                        )
                }
            );


        const result =
            await response.json();


        if (!response.ok)
        {
            throw new Error(
                result.error
            );
        }


        message.textContent =
            "Schedule saved.";


        formLoaded = false;


        refresh();
    }

    catch(error)
    {
        message.textContent =
            "Error: "
            +
            error.message;
    }
}


refresh();

setInterval(
    refresh,
    500
);

</script>

</body>
</html>
"""


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def home():

    return HTML


@app.route("/api/status")
def status():

    return jsonify(
        get_state()
    )


@app.route(
    "/api/pir2/schedule",
    methods=["POST"]
)
def pir2_schedule():

    data = request.get_json(
        silent=True
    ) or {}


    enabled = bool(
        data.get(
            "enabled",
            False
        )
    )


    start = str(
        data.get(
            "start_time",
            ""
        )
    )


    end = str(
        data.get(
            "end_time",
            ""
        )
    )


    if not valid_time(
        start
    ):

        return jsonify(
            {
                "error":
                    "Invalid start time"
            }
        ), 400


    if not valid_time(
        end
    ):

        return jsonify(
            {
                "error":
                    "Invalid end time"
            }
        ), 400


    save_data = {
        "enabled": enabled,
        "start_time": start,
        "end_time": end
    }


    with open(
        PIR2_SCHEDULE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            save_data,
            file,
            indent=2
        )


    update_state(
        pir2_enabled=enabled,
        pir2_start_time=start,
        pir2_end_time=end
    )


    return jsonify(
        {
            "ok": True
        }
    )


# =========================================================
# RUN
# =========================================================

def run_dashboard():

    print()
    print("============================================")
    print("             WEB DASHBOARD")
    print("============================================")
    print(
        f"Port: {WEB_PORT}"
    )


    app.run(
        host=WEB_HOST,
        port=WEB_PORT,
        debug=False,
        use_reloader=False,
        threaded=True
    )
