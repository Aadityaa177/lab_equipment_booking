
document.addEventListener("DOMContentLoaded", () => {
    const dateInput = document.getElementById("booking-date");
    const slotSelect = document.getElementById("slot-id");
    const availabilityForm = document.getElementById("availability-form");
    const bookingForm = document.getElementById("booking-form");
    const computerList = document.getElementById("computer-list");
    const message = document.getElementById("booking-message");
    const selectionHelp = document.getElementById("selection-help");

    const role = window.USER_ROLE;
    const isFaculty = role === "FACULTY";

    // Default to tomorrow.
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dateInput.value = [
        tomorrow.getFullYear(),
        String(tomorrow.getMonth() + 1).padStart(2, "0"),
        String(tomorrow.getDate()).padStart(2, "0")
    ].join("-");

    dateInput.min = new Date().toISOString().slice(0, 10);

    selectionHelp.textContent = isFaculty
        ? "Faculty may select multiple computers."
        : "Students may select one computer per booking.";

    async function loadSlots() {
        try {
            const response = await fetch("/api/timetable-slots");
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Could not load timetable.");
            }

            slotSelect.replaceChildren(new Option("Choose a period", ""));

            data.slots.forEach(slot => {
                const option = new Option(
                    `${slot.day_of_week} — ${slot.slot_code} (${slot.display_label})`,
                    slot.slot_id
                );
                slotSelect.add(option);
            });

            if (window.SELECTED_SLOT_ID) {
                slotSelect.value = String(window.SELECTED_SLOT_ID);
            }
        } catch (error) {
            message.textContent = error.message;
        }
    }

    availabilityForm.addEventListener("submit", async event => {
        event.preventDefault();
        bookingForm.hidden = true;
        computerList.replaceChildren();
        message.textContent = "Checking availability...";

        const date = dateInput.value;
        const slotId = slotSelect.value;

        try {
            const response = await fetch(
                `/api/computers/available?date=${encodeURIComponent(date)}&slot_id=${encodeURIComponent(slotId)}`
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Could not fetch availability.");
            }

            if (!data.available_computers.length) {
                message.textContent = "No healthy computers are available for this period.";
                return;
            }

            data.available_computers.forEach(computer => {
                const label = document.createElement("label");
                label.className = "computer-option";

                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.name = "computer";
                checkbox.value = computer.computer_id;

                const text = document.createElement("span");
                text.textContent = `${computer.computer_code} — ${computer.lab_name}`;

                label.append(checkbox, text);
                computerList.append(label);
            });

            message.textContent =
                `${data.available_computers.length} healthy computer(s) available.`;

            bookingForm.hidden = false;
        } catch (error) {
            message.textContent = error.message;
        }
    });

    computerList.addEventListener("change", event => {
        if (!isFaculty && event.target.matches('input[name="computer"]')) {
            if (event.target.checked) {
                computerList.querySelectorAll('input[name="computer"]').forEach(input => {
                    if (input !== event.target) input.checked = false;
                });
            }
        }
    });

    bookingForm.addEventListener("submit", async event => {
        event.preventDefault();

        const computerIds = Array.from(
            computerList.querySelectorAll('input[name="computer"]:checked')
        ).map(input => Number(input.value));

        if (!computerIds.length) {
            message.textContent = "Select at least one computer.";
            return;
        }

        if (!isFaculty && computerIds.length !== 1) {
            message.textContent = "Students can book only one computer.";
            return;
        }

        message.textContent = "Saving booking...";

        try {
            const response = await fetch("/api/bookings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                user_id: window.CAMPUS_USER_ID,
                date: dateInput.value,
                slot_ids: [Number(slotSelect.value)],
                computer_ids: computerIds,
                purpose: document.getElementById("purpose").value.trim()
            })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Booking failed.");
            }

            message.textContent = data.message || "Booking confirmed!";
            bookingForm.hidden = true;
        } catch (error) {
            message.textContent = error.message;
        }
    });

    loadSlots();
});
