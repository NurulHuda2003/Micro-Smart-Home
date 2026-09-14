# =========================================================
# SOFTWARE NOTIFICATION MODULE
# =========================================================
#
# এই file-এর কাজ:
#
# Raspberry Pi security controller থেকে software/backend
# notification system-এর জন্য event পাঠানোর জায়গা রাখা।
#
# পরে তোমার software তৈরি হলে এই function-এর ভিতরে
# তোমার API code বসবে।
# =========================================================


def send_unknown_notification():

    print()
    print("============================================")
    print("       SOFTWARE NOTIFICATION EVENT")
    print("============================================")

    print(
        "Unknown person detected at the door."
    )

    print(
        "Notification should be sent to owner."
    )

    print("============================================")
    print()


    # =====================================================
    # FUTURE SOFTWARE IMPLEMENTATION
    # =====================================================
    #
    # পরে এখানে তোমার backend/API call বসবে।
    #
    # Example structure:
    #
    # requests.post(
    #     "YOUR_SERVER_API",
    #     json={
    #         "event": "unknown_person"
    #     }
    # )
    #
    # এখন কোনো API দেওয়া হয়নি কারণ software/backend
    # এখনো তৈরি হয়নি।
    # =====================================================


def send_forced_entry_notification():

    print()
    print("============================================")
    print("          FORCED ENTRY EVENT")
    print("============================================")

    print(
        "Unauthorized door opening detected."
    )

    print("============================================")
    print()