import logging


from flask import (
    Flask,
    jsonify,
    make_response
)


from config import (
    WEB_HOST,
    WEB_PORT
)


from system_state import (
    get_state
)


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)


# Hide repeated Flask GET logs
logging.getLogger(
    "werkzeug"
).setLevel(
    logging.ERROR
)


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
def index():

    html = """
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
Smart Safety System
</title>


<style>

* {
    box-sizing: border-box;
}


body {

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        #f3f6fa;

    color:
        #172033;
}


header {

    background:
        #111827;

    color:
        white;

    padding:
        28px 20px;

    text-align:
        center;
}


header h1 {

    margin:
        0;

    font-size:
        30px;
}


header p {

    color:
        #cbd5e1;

    margin-bottom:
        0;
}


.container {

    width:
        94%;

    max-width:
        1200px;

    margin:
        25px auto;
}


.section {

    background:
        white;

    border-radius:
        14px;

    padding:
        22px;

    margin-bottom:
        22px;

    box-shadow:
        0 3px 15px
        rgba(0,0,0,.08);
}


.section-header {

    display:
        flex;

    justify-content:
        space-between;

    align-items:
        center;

    gap:
        10px;

    margin-bottom:
        20px;
}


.section-header h2 {

    margin: 0;
}


.grid {

    display:
        grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                170px,
                1fr
            )
        );

    gap:
        14px;
}


.card {

    background:
        #f8fafc;

    border:
        1px solid
        #e2e8f0;

    border-radius:
        12px;

    padding:
        18px;
}


.label {

    color:
        #64748b;

    font-size:
        13px;
}


.value {

    margin-top:
        8px;

    font-size:
        24px;

    font-weight:
        bold;
}


.badge {

    padding:
        7px 12px;

    border-radius:
        20px;

    font-size:
        12px;

    font-weight:
        bold;
}


.connected {

    color:
        #166534;

    background:
        #dcfce7;
}


.disconnected {

    color:
        #991b1b;

    background:
        #fee2e2;
}


.status-line {

    font-size:
        14px;

    color:
        #64748b;
}


footer {

    text-align:
        center;

    color:
        #64748b;

    padding:
        0 0 30px;
}


</style>

</head>


<body>


<header>

<h1>
Smart Safety & Security System
</h1>

<p>
Raspberry Pi + ESP32 Central Monitoring
</p>

</header>



<div class="container">


<!-- ================================================= -->
<!-- KITCHEN -->
<!-- ================================================= -->

<div class="section">


<div class="section-header">

<h2>
Kitchen Safety
</h2>


<span
    id="esp32Badge"
    class="badge disconnected"
>
ESP32 DISCONNECTED
</span>

</div>


<div class="grid">


<div class="card">

<div class="label">
Gas ADC
</div>

<div
    class="value"
    id="gasADC"
>
0
</div>

</div>



<div class="card">

<div class="label">
Approx Gas PPM
</div>

<div
    class="value"
    id="gasPPM"
>
0
</div>

</div>



<div class="card">

<div class="label">
Gas Status
</div>

<div
    class="value"
    id="gasStatus"
>
SAFE
</div>

</div>



<div class="card">

<div class="label">
Flame
</div>

<div
    class="value"
    id="flameStatus"
>
NORMAL
</div>

</div>



<div class="card">

<div class="label">
Kitchen State
</div>

<div
    class="value"
    id="kitchenState"
>
WAITING
</div>

</div>



<div class="card">

<div class="label">
Water Pump
</div>

<div
    class="value"
    id="pumpStatus"
>
OFF
</div>

</div>



<div class="card">

<div class="label">
Kitchen Buzzer
</div>

<div
    class="value"
    id="kitchenBuzzer"
>
OFF
</div>

</div>



<div class="card">

<div class="label">
ESP32 Data Age
</div>

<div
    class="value"
    id="espAge"
>
-
</div>

</div>


</div>

</div>



<!-- ================================================= -->
<!-- SECURITY -->
<!-- ================================================= -->

<div class="section">


<div class="section-header">

<h2>
Door Security
</h2>

<span
    class="badge connected"
>
PI ONLINE
</span>

</div>


<div class="grid">


<div class="card">

<div class="label">
Motion
</div>

<div
    class="value"
    id="motion"
>
NONE
</div>

</div>



<div class="card">

<div class="label">
Camera
</div>

<div
    class="value"
    id="camera"
>
OFF
</div>

</div>



<div class="card">

<div class="label">
Face
</div>

<div
    class="value"
    id="face"
>
WAITING
</div>

</div>



<div class="card">

<div class="label">
Person
</div>

<div
    class="value"
    id="person"
>
-
</div>

</div>



<div class="card">

<div class="label">
Score
</div>

<div
    class="value"
    id="score"
>
0.000
</div>

</div>



<div class="card">

<div class="label">
Gate
</div>

<div
    class="value"
    id="gate"
>
LOCKED
</div>

</div>



<div class="card">

<div class="label">
Security Buzzer
</div>

<div
    class="value"
    id="piBuzzer"
>
OFF
</div>

</div>


</div>

</div>



<div class="section">

<div class="status-line">

API:
<span id="apiStatus">
Connecting...
</span>

</div>

<br>

<div class="status-line">

Last dashboard refresh:
<span id="lastRefresh">
-
</span>

</div>

</div>


</div>


<footer>

Auto refresh every 500 ms

</footer>



<script>


// =========================================================
// HELPER
// =========================================================

function setValue(
    id,
    value
)
{
    document.getElementById(
        id
    ).textContent =
        value;
}


// =========================================================
// ESP32 BADGE
// =========================================================

function setESP32Connection(
    connected
)
{
    const badge =
        document.getElementById(
            "esp32Badge"
        );


    if (connected)
    {
        badge.textContent =
            "ESP32 CONNECTED";

        badge.className =
            "badge connected";
    }

    else
    {
        badge.textContent =
            "ESP32 DISCONNECTED";

        badge.className =
            "badge disconnected";
    }
}


// =========================================================
// REFRESH
// =========================================================

async function refreshDashboard()
{
    try
    {
        const response =
            await fetch(

                "/api/status?t="
                +
                Date.now(),

                {
                    cache:
                        "no-store"
                }
            );


        if (!response.ok)
        {
            throw new Error(
                "HTTP "
                +
                response.status
            );
        }


        const data =
            await response.json();


        // =================================================
        // KITCHEN
        // =================================================

        setESP32Connection(
            data.esp32_connected
        );


        setValue(
            "gasADC",
            data.gas_adc
        );


        setValue(
            "gasPPM",
            data.gas_ppm
        );


        setValue(

            "gasStatus",

            data.gas_detected
                ?
                "DETECTED"
                :
                "SAFE"
        );


        setValue(

            "flameStatus",

            data.flame_detected
                ?
                "FIRE"
                :
                "NORMAL"
        );


        setValue(
            "kitchenState",
            data.esp32_state
        );


        setValue(
            "pumpStatus",
            data.pump
        );


        setValue(
            "kitchenBuzzer",
            data.esp32_buzzer
        );


        if (
            data.esp32_age
            ===
            null
        )
        {
            setValue(
                "espAge",
                "-"
            );
        }

        else
        {
            setValue(

                "espAge",

                data.esp32_age
                +
                " sec"
            );
        }


        // =================================================
        // PI SECURITY
        // =================================================

        setValue(

            "motion",

            data.motion
                ?
                "DETECTED"
                :
                "NONE"
        );


        setValue(
            "camera",
            data.camera
        );


        setValue(
            "face",
            data.face_status
        );


        setValue(
            "person",
            data.person
        );


        setValue(

            "score",

            Number(
                data.face_score
                ||
                0
            ).toFixed(
                3
            )
        );


        setValue(
            "gate",
            data.gate
        );


        setValue(
            "piBuzzer",
            data.pi_buzzer
        );


        // =================================================
        // STATUS
        // =================================================

        setValue(
            "apiStatus",
            "CONNECTED"
        );


        setValue(

            "lastRefresh",

            new Date()
            .toLocaleTimeString()
        );
    }


    catch(error)
    {
        console.error(
            error
        );


        setValue(
            "apiStatus",
            "ERROR"
        );


        setESP32Connection(
            false
        );
    }
}


// Immediate update

refreshDashboard();


// Auto update every 500ms

setInterval(
    refreshDashboard,
    500
);


</script>


</body>

</html>
"""


    response = make_response(
        html
    )


    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, max-age=0"
    )


    return response


# =========================================================
# API
# =========================================================

@app.route(
    "/api/status"
)
def api_status():

    response = jsonify(
        get_state()
    )


    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, max-age=0"
    )


    return response


# =========================================================
# RUN
# =========================================================

def run_dashboard():

    print()
    print("============================================")
    print("             WEB DASHBOARD")
    print("============================================")

    print(
        f"http://localhost:{WEB_PORT}"
    )


    app.run(

        host=WEB_HOST,

        port=WEB_PORT,

        debug=False,

        use_reloader=False,

        threaded=True
    )
