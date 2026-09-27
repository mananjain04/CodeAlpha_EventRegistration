from flask import Flask, jsonify, render_template, request
import database

app = Flask(__name__)


# 1. Homepage Route (Frontend UI load karega)
@app.route("/")
def home():
    try:
        return render_template("index.html")
    except Exception:
        return """
        <h2>Event Registration System API is Running! 🎟️</h2>
        <p>Frontend template bante hi UI yahan load ho jayega.</p>
        """


# 2. API: Saare events dekhne ke liye (List)
@app.route("/api/events", methods=["GET"])
def get_events():
    events = database.get_all_events()
    return jsonify({"success": True, "events": events})


# 3. API: Kisi specific event ki details dekhne ke liye
@app.route("/api/events/<int:event_id>", methods=["GET"])
def get_single_event(event_id):
    event = database.get_event_by_id(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    return jsonify({"success": True, "event": event})


# 4. API: Event ke liye Register karna (POST)
@app.route("/api/events/<int:event_id>/register", methods=["POST"])
def register_for_event(event_id):
    data = request.get_json(silent=True) or request.form

    user_name = data.get("name", "").strip()
    user_email = data.get("email", "").strip()

    # Validation
    if not user_name or not user_email:
        return jsonify({"error": "Name and Email are required!"}), 400

    # Database mein registration save karo
    success, message = database.register_user(event_id, user_name, user_email)

    if not success:
        return jsonify({"error": message}), 400

    return jsonify({"success": True, "message": message}), 201


# 5. API: User ke booked events dekhna (View Registrations)
@app.route("/api/registrations", methods=["GET"])
def user_registrations():
    email = request.args.get("email", "").strip()
    if not email:
        return jsonify({"error": "Email parameter is required!"}), 400

    registrations = database.get_user_registrations(email)
    return jsonify({"success": True, "registrations": registrations})


# 6. API: Registration Cancel karna (DELETE)
@app.route("/api/registrations/<int:reg_id>", methods=["DELETE"])
def cancel_ticket(reg_id):
    deleted = database.cancel_registration(reg_id)
    if not deleted:
        return (
            jsonify({"error": "Registration not found or already cancelled"}),
            404,
        )

    return jsonify(
        {"success": True, "message": "Registration cancelled successfully!"}
    )


# ---------------- SERVER START ---------------- #
if __name__ == "__main__":
    database.init_db()  # DB ensure karo
    print("Event Registration Server running at http://127.0.0.1:5000 ...")
    app.run(port=5000, debug=True)